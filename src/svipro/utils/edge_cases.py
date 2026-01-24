"""
Edge case handling utilities for SVIPro.

This module provides utilities for handling edge cases and boundary
conditions in spatial sampling operations.
"""

from typing import Optional, Tuple, Union
import logging
import warnings
from shapely.geometry import Polygon, Point, box, MultiPolygon
from shapely.geometry.base import BaseGeometry
import geopandas as gpd
import numpy as np

from svipro.exceptions import BoundaryError, ValidationError, ConfigurationError


logger = logging.getLogger(__name__)


def handle_small_boundary(
    boundary: Polygon,
    spacing: float,
    min_area_ratio: float = 0.1
) -> Tuple[Polygon, bool]:
    """
    Handle boundaries that are too small for the given spacing.

    Args:
        boundary: The input boundary polygon
        spacing: The sampling spacing in meters
        min_area_ratio: Minimum ratio of boundary area to spacing area
                       (default: 0.1, meaning boundary should be at least
                        10% of the area of one grid cell)

    Returns:
        Tuple of (processed_boundary, was_modified)

    Raises:
        BoundaryError: If boundary is too small and cannot be fixed

    Example:
        >>> boundary = box(0, 0, 50, 50)  # Very small area
        >>> processed, modified = handle_small_boundary(boundary, spacing=100)
        >>> if modified:
        ...     print("Boundary was too small, adjusted automatically")
    """
    boundary_area = boundary.area
    spacing_area = spacing * spacing
    area_ratio = boundary_area / spacing_area

    # If boundary is reasonably large, return as-is
    if area_ratio >= min_area_ratio:
        return boundary, False

    # Boundary is too small
    logger.warning(
        f"Boundary area ({boundary_area:.2f}) is very small compared "
        f"to spacing² ({spacing_area:.2f}). Area ratio: {area_ratio:.3f}"
    )

    # Try to expand boundary slightly
    if area_ratio > 0.01:  # At least 1% of spacing area
        # Expand by one spacing in each direction
        minx, miny, maxx, maxy = boundary.bounds
        expanded = box(
            minx - spacing/2,
            miny - spacing/2,
            maxx + spacing/2,
            maxy + spacing/2
        )

        logger.info(f"Expanded boundary to ensure at least one sample point")
        return expanded, True

    # Boundary is extremely small, raise error
    raise BoundaryError(
        f"Boundary area too small for specified spacing. "
        f"Boundary area: {boundary_area:.6f}, spacing: {spacing}m. "
        f"Please use a larger boundary or smaller spacing.",
        details={
            'boundary_area': boundary_area,
            'spacing_m': spacing,
            'area_ratio': area_ratio,
            'min_required_ratio': min_area_ratio
        }
    )


def fix_invalid_geometry(
    geometry: BaseGeometry,
    max_buffer_distance: float = 0.0001,
    min_area_threshold: float = 1e-10
) -> BaseGeometry:
    """
    Attempt to fix invalid geometries.

    Args:
        geometry: The input geometry (may be invalid)
        max_buffer_distance: Maximum buffer distance for fixing (in degrees)
        min_area_threshold: Minimum acceptable area for fixed geometries

    Returns:
        Fixed geometry (may be different type if invalid)

    Raises:
        BoundaryError: If geometry cannot be fixed

    Example:
        >>> invalid_poly = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])
        >>> fixed = fix_invalid_geometry(invalid_poly)
        >>> assert fixed.is_valid
    """
    def has_sufficient_area(geom: BaseGeometry) -> bool:
        """Check if geometry has sufficient area for practical use."""
        if geom.is_empty:
            return False
        if isinstance(geom, Polygon):
            return geom.area > min_area_threshold
        return True

    if geometry.is_valid:
        # Check if it's a valid but empty/zero-area geometry
        if not has_sufficient_area(geometry):
            raise BoundaryError(
                "Geometry is valid but has insufficient area. "
                "Please provide a polygon with non-zero area.",
                details={
                    'geometry_type': geometry.geom_type,
                    'is_valid': geometry.is_valid,
                    'is_empty': geometry.is_empty,
                    'area': getattr(geometry, 'area', None),
                    'min_area_threshold': min_area_threshold
                }
            )
        return geometry

    logger.warning(f"Invalid geometry detected, attempting to fix")

    # Try buffer(0) fix
    try:
        fixed = geometry.buffer(0)
        if fixed.is_valid and has_sufficient_area(fixed):
            logger.info("Fixed invalid geometry using buffer(0)")
            return fixed
    except Exception as e:
        logger.warning(f"buffer(0) fix failed: {e}")

    # Try small positive buffer
    try:
        fixed = geometry.buffer(max_buffer_distance)
        if fixed.is_valid and has_sufficient_area(fixed):
            logger.info(f"Fixed invalid geometry using buffer({max_buffer_distance})")
            return fixed
    except Exception as e:
        logger.warning(f"buffer fix failed: {e}")

    # Try convex hull as last resort
    try:
        if hasattr(geometry, 'convex_hull'):
            fixed = geometry.convex_hull
            if fixed.is_valid and has_sufficient_area(fixed):
                logger.info("Fixed invalid geometry using convex hull")
                return fixed
    except Exception as e:
        logger.warning(f"convex_hull fix failed: {e}")

    raise BoundaryError(
        "Could not fix invalid geometry. "
        "Please check your boundary for topological errors.",
        details={
            'geometry_type': geometry.geom_type,
            'is_valid': geometry.is_valid,
            'is_empty': geometry.is_empty
        }
    )


def ensure_polygon(
    geometry: BaseGeometry,
    allow_multipolygon: bool = True
) -> Polygon:
    """
    Ensure geometry is a (Multi)Polygon.

    Args:
        geometry: Input geometry (any type)
        allow_multipolygon: Whether to accept MultiPolygon (default: True)

    Returns:
        Polygon (or MultiPolygon if allowed and applicable)

    Raises:
        BoundaryError: If geometry cannot be converted to Polygon

    Example:
        >>> point = Point(0, 0)
        >>> poly = ensure_polygon(point.buffer(0.01))
        >>> isinstance(poly, Polygon)
    """
    if isinstance(geometry, Polygon):
        return geometry

    if isinstance(geometry, MultiPolygon):
        if allow_multipolygon:
            return geometry
        else:
            # Merge to single polygon
            geoms_list = list(geometry.geoms)
            if len(geoms_list) == 1:
                return geoms_list[0]
            else:
                # Use unary_union to merge
                merged = geoms_list[0]
                for geom in geoms_list[1:]:
                    merged = merged.union(geom)
                return merged

    # Try to buffer points/lines to create polygon
    try:
        buffered = geometry.buffer(0.0001)  # Small buffer
        if isinstance(buffered, (Polygon, MultiPolygon)):
            return ensure_polygon(buffered, allow_multipolygon)
    except Exception as e:
        logger.warning(f"Could not buffer geometry: {e}")

    raise BoundaryError(
        f"Geometry must be a Polygon, got {geometry.geom_type}. "
        f"Please provide a valid polygon boundary.",
        details={
            'input_type': geometry.geom_type,
            'allow_multipolygon': allow_multipolygon
        }
    )


def validate_crs_compatibility(
    boundary_crs: str,
    target_crs: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate if two coordinate systems are compatible for operations.

    Args:
        boundary_crs: CRS of the boundary geometry
        target_crs: Target CRS for operations

    Returns:
        Tuple of (is_compatible, warning_message)

    Example:
        >>> compatible, warning = validate_crs_compatibility('EPSG:4326', 'EPSG:3857')
        >>> if not compatible:
        ...     print(warning)
    """
    # Geographic CRS (lat/lon)
    geographic_crs = {'EPSG:4326', 'EPSG:4269', 'EPSG:4632'}

    # Projected CRS (meters)
    projected_crs = {'EPSG:3857', 'EPSG:32633', 'EPSG:32634'}

    boundary_is_geographic = boundary_crs in geographic_crs
    target_is_geographic = target_crs in geographic_crs

    if boundary_crs == target_crs:
        return True, None

    # Different types - will need transformation
    if boundary_is_geographic != target_is_geographic:
        return False, (
            f"CRS mismatch: boundary is in '{boundary_crs}' "
            f"(geographic={boundary_is_geographic}), "
            f"target is '{target_crs}' (geographic={target_is_geographic}). "
            f"Accuracy may be affected."
        )

    return True, None


def handle_empty_geodataframe(
    gdf: gpd.GeoDataFrame,
    operation: str = "operation"
) -> gpd.GeoDataFrame:
    """
    Handle empty GeoDataFrame edge cases.

    Args:
        gdf: The GeoDataFrame to check
        operation: Description of the operation being performed

    Returns:
        The same GeoDataFrame (or raises error if empty and not allowed)

    Raises:
        ValidationError: If GeoDataFrame is empty

    Example:
        >>> if len(points_gdf) == 0:
        ...     points_gdf = handle_empty_geodataframe(points_gdf, "sampling")
    """
    if len(gdf) == 0:
        raise ValidationError(
            f"Empty GeoDataFrame passed to {operation}. "
            f"Cannot proceed with empty data.",
            details={
                'operation': operation,
                'columns': list(gdf.columns),
                'crs': str(gdf.crs)
            }
        )

    return gdf


def warn_large_output(
    n_points: int,
    max_recommended: int = 10000
) -> None:
    """
    Warn user if output size is very large.

    Args:
        n_points: Number of sample points being generated
        max_recommended: Maximum recommended points before warning

    Example:
        >>> warn_large_output(n_points=50000)
        ⚠️ Warning: Generating 50000 points...
    """
    if n_points > max_recommended:
        warnings.warn(
            f"Generating {n_points} sample points, which exceeds the "
            f"recommended maximum of {max_recommended}. "
            f"This may take longer and use more memory.",
            UserWarning
        )


def estimate_processing_time(
    n_points: int,
    strategy: str = "grid"
) -> float:
    """
    Estimate processing time for sampling operation.

    Args:
        n_points: Number of sample points to generate
        strategy: Sampling strategy name

    Returns:
        Estimated time in seconds

    Example:
        >>> time_est = estimate_processing_time(1000, "grid")
        >>> print(f"Estimated time: {time_est:.1f} seconds")
    """
    # Base time estimates per point (in seconds)
    base_times = {
        'grid': 0.0001,      # Very fast
        'road_network': 0.01,  # Slower due to OSM download
        'random': 0.0005,
        'optimized': 0.005
    }

    time_per_point = base_times.get(strategy, 0.001)
    return n_points * time_per_point


def check_spacing_bounds(
    spacing: float,
    min_spacing: float = 1.0,
    max_spacing: float = 10000.0
) -> None:
    """
    Check if spacing value is within reasonable bounds.

    Args:
        spacing: The spacing value to check
        min_spacing: Minimum reasonable spacing (default: 1 meter)
        max_spacing: Maximum reasonable spacing (default: 10 km)

    Raises:
        ConfigurationError: If spacing is out of bounds

    Example:
        >>> check_spacing_bounds(5000)  # OK
        >>> check_spacing_bounds(0.1)   # Raises error
    """
    if spacing < min_spacing:
        raise ConfigurationError(
            f"Spacing too small: {spacing}m. Minimum is {min_spacing}m.",
            details={
                'spacing_m': spacing,
                'min_spacing_m': min_spacing,
                'max_spacing_m': max_spacing
            }
        )

    if spacing > max_spacing:
        raise ConfigurationError(
            f"Spacing too large: {spacing}m. Maximum is {max_spacing}m.",
            details={
                'spacing_m': spacing,
                'min_spacing_m': min_spacing,
                'max_spacing_m': max_spacing
            }
        )


def safe_geometry_operation(
    operation_name: str,
    operation_func,
    geometry: BaseGeometry,
    fallback_value = None
) -> Union[BaseGeometry, any]:
    """
    Safely execute geometry operations with error handling.

    Args:
        operation_name: Description of the operation
        operation_func: Function to execute
        geometry: Geometry to operate on
        fallback_value: Value to return if operation fails

    Returns:
        Operation result or fallback value

    Example:
        >>> def calculate_area(g):
        ...     return g.area
        >>> area = safe_geometry_operation("area calculation", calculate_area, poly)
    """
    try:
        return operation_func(geometry)
    except Exception as e:
        logger.error(f"Failed to {operation_name}: {e}")
        if fallback_value is not None:
            return fallback_value
        raise BoundaryError(
            f"Failed to {operation_name}: {e}",
            details={'operation': operation_name, 'geometry_type': geometry.geom_type}
        )
