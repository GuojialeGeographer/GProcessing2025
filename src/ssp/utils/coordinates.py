"""
Coordinate Utilities Module

Provides utility functions for converting between different units and coordinate systems.
This is essential for accurate spatial sampling when working with geographic coordinates.
"""

import math
from typing import Tuple, Optional


def meters_to_degrees(
    meters: float,
    latitude: Optional[float] = None
) -> float:
    """
    Convert meters to degrees for approximate spacing conversion.

    This function converts a distance in meters to its equivalent in degrees
    of longitude/latitude. The conversion varies with latitude because the
    length of a degree of longitude changes with latitude.

    Args:
        meters: Distance in meters to convert to degrees.
        latitude: Optional latitude in degrees for longitude conversion.
                 If None, uses a default conversion at 45° latitude.
                 Only affects longitude conversion.

    Returns:
        Approximate distance in degrees.

    Note:
        This is an approximation suitable for sampling spacing.
        For precise geodetic calculations, use pyproj or similar libraries.

        At the equator:
        - 1 degree latitude ≈ 110,574 meters
        - 1 degree longitude ≈ 111,320 meters

        At 45° latitude:
        - 1 degree latitude ≈ 110,574 meters
        - 1 degree longitude ≈ 78,847 meters

        At the poles:
        - 1 degree latitude ≈ 110,574 meters (constant)
        - 1 degree longitude ≈ 0 meters (converges)

    Example:
        >>> # At default latitude (45°)
        >>> degrees = meters_to_degrees(100)  # 100 meters to degrees
        >>> # For longitude at specific latitude
        >>> degrees = meters_to_degrees(100, latitude=35.5)  # Milan
    """
    if meters == 0:
        return 0.0

    if latitude is None:
        latitude = 45.0  # Default to mid-latitude

    # 1 degree of latitude is approximately 111,132 meters on average
    # This is relatively constant across latitudes
    meters_per_degree_lat = 111132.0

    # 1 degree of longitude varies with latitude
    # At the equator: ~111,320 meters
    # Formula: 111320 * cos(latitude)
    lat_rad = math.radians(latitude)
    meters_per_degree_lon = 111320.0 * math.cos(lat_rad)

    # Use the average for simplicity in grid spacing
    # This provides a reasonable approximation for most use cases
    avg_meters_per_degree = (meters_per_degree_lat + meters_per_degree_lon) / 2

    degrees = meters / avg_meters_per_degree

    return degrees


def degrees_to_meters(
    degrees: float,
    latitude: Optional[float] = None
) -> float:
    """
    Convert degrees to meters for approximate distance conversion.

    This function converts a distance in degrees to its equivalent in meters.
    The conversion varies with latitude because the length of a degree of
    longitude changes with latitude.

    Args:
        degrees: Distance in degrees to convert to meters.
        latitude: Optional latitude in degrees for longitude conversion.
                 If None, uses a default conversion at 45° latitude.

    Returns:
        Approximate distance in meters.

    Example:
        >>> # At default latitude (45°)
        >>> meters = degrees_to_meters(0.001)
        >>> # For longitude at specific latitude
        >>> meters = degrees_to_meters(0.001, latitude=35.5)
    """
    if degrees == 0:
        return 0.0

    if latitude is None:
        latitude = 45.0

    # Use the same conversion factors as meters_to_degrees
    meters_per_degree_lat = 111132.0
    lat_rad = math.radians(latitude)
    meters_per_degree_lon = 111320.0 * math.cos(lat_rad)

    avg_meters_per_degree = (meters_per_degree_lat + meters_per_degree_lon) / 2

    meters = degrees * avg_meters_per_degree

    return meters


def estimate_center_latitude(boundary) -> float:
    """
    Estimate the center latitude of a boundary polygon.

    Args:
        boundary: Shapely Polygon object.

    Returns:
        Center latitude in degrees.

    Example:
        >>> from shapely.geometry import box
        >>> bounds = box(9.0, 45.0, 10.0, 46.0)
        >>> center_lat = estimate_center_latitude(bounds)
        >>> assert center_lat == 45.5
    """
    miny = boundary.bounds[1]
    maxy = boundary.bounds[3]
    return (miny + maxy) / 2


def convert_spacing_for_crs(
    spacing_meters: float,
    crs: str,
    boundary=None
) -> float:
    """
    Convert spacing from meters to appropriate units for the CRS.

    This function converts spacing in meters to the units used by the
    specified coordinate reference system. For EPSG:4326 (WGS84),
    this converts meters to degrees. For projected coordinate systems,
    it returns meters unchanged.

    Args:
        spacing_meters: Spacing in meters.
        crs: Coordinate reference system (e.g., 'EPSG:4326', 'EPSG:3857').
        boundary: Optional boundary for estimating latitude in EPSG:4326.

    Returns:
        Spacing in the appropriate units for the CRS.

    Example:
        >>> # For geographic coordinates (WGS84)
        >>> spacing = convert_spacing_for_crs(100, 'EPSG:4326')
        >>> # For projected coordinates
        >>> spacing = convert_spacing_for_crs(100, 'EPSG:3857')
    """
    if spacing_meters == 0:
        return 0.0

    # EPSG:4326 is WGS84 geographic coordinates (degrees)
    if crs.upper() == 'EPSG:4326':
        latitude = None
        if boundary is not None:
            latitude = estimate_center_latitude(boundary)
        return meters_to_degrees(spacing_meters, latitude)

    # For projected coordinate systems that use meters
    # Return spacing unchanged
    return spacing_meters
