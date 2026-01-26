"""
Base Sampling Strategy Module

This module defines the abstract interface for all sampling strategies used in SpatialSamplingPro.
It ensures reproducibility, standardization, and consistency across different sampling methods.

All sampling strategies must inherit from SamplingStrategy and implement the generate() method.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import geopandas as gpd
from shapely.geometry import Point, Polygon
import warnings

from ssp.exceptions import (
    ConfigurationError,
    BoundaryError,
    SamplingError
)


@dataclass
class SamplingConfig:
    """
    Configuration for sampling strategy.

    This dataclass encapsulates all parameters needed for spatial sampling,
    including spacing, coordinate system, random seed, and metadata.

    Attributes:
        spacing: Distance between sample points in meters. Must be positive.
        crs: Coordinate Reference System as EPSG code (e.g., "EPSG:4326").
        seed: Random seed for reproducibility. Default is 42.
        boundary: Optional area of interest as shapely Polygon.
        metadata: Additional metadata dictionary for custom parameters.

    Raises:
        ValueError: If spacing is not positive.
        ValueError: If crs is not a valid string.

    Example:
        >>> from shapely.geometry import box
        >>> config = SamplingConfig(
        ...     spacing=100.0,
        ...     crs="EPSG:4326",
        ...     seed=42,
        ...     boundary=box(0, 0, 1000, 1000)
        ... )
        >>> config_dict = config.to_dict()
    """
    spacing: float = 100.0
    crs: str = "EPSG:4326"
    seed: int = 42
    boundary: Optional[Polygon] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration parameters after initialization."""
        self._validate()

    def _validate(self) -> None:
        """
        Validate configuration parameters.

        Raises:
            ConfigurationError: If spacing is not positive.
            ConfigurationError: If crs is empty or invalid.
            ConfigurationError: If seed is negative.
        """
        if self.spacing <= 0:
            raise ConfigurationError(
                f"spacing must be positive (got {self.spacing}). "
                "Spacing represents distance in meters between sample points.",
                details={'spacing': self.spacing, 'valid_range': '(0, inf)'}
            )

        if not self.crs or not isinstance(self.crs, str):
            raise ConfigurationError(
                f"crs must be a non-empty string (got '{self.crs}'). "
                "Expected format: 'EPSG:XXXX' (e.g., 'EPSG:4326').",
                details={'crs': self.crs, 'expected_format': 'EPSG:XXXX'}
            )

        if self.seed < 0:
            raise ConfigurationError(
                f"seed must be non-negative (got {self.seed}). "
                "Seed is used for reproducibility.",
                details={'seed': self.seed, 'valid_range': '[0, inf)'}
            )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary for serialization.

        Returns:
            Dictionary containing all configuration parameters with
            boundary converted to WKT format if present.

        Example:
            >>> config = SamplingConfig(spacing=100.0)
            >>> config_dict = config.to_dict()
            >>> assert config_dict['spacing'] == 100.0
        """
        return {
            'spacing': self.spacing,
            'crs': self.crs,
            'seed': self.seed,
            'boundary': self.boundary.wkt if self.boundary else None,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SamplingConfig':
        """
        Create configuration from dictionary.

        Args:
            data: Dictionary containing configuration parameters.

        Returns:
            SamplingConfig instance.

        Raises:
            ValueError: If required keys are missing.
            KeyError: If boundary WKT is invalid.

        Example:
            >>> data = {'spacing': 100.0, 'crs': 'EPSG:4326', 'seed': 42}
            >>> config = SamplingConfig.from_dict(data)
        """
        from shapely import wkt

        required_keys = ['spacing', 'crs', 'seed']
        missing_keys = [k for k in required_keys if k not in data]
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")

        config_data = data.copy()

        # Convert WKT back to Polygon if present
        if config_data.get('boundary'):
            config_data['boundary'] = wkt.loads(config_data['boundary'])

        return cls(**config_data)


class SamplingStrategy(ABC):
    """
    Abstract base class for sampling strategies.

    This class defines the interface that all sampling strategies must implement.
    It ensures consistent API, reproducibility, and standardization across different
    spatial sampling methods.

    All strategies must inherit from this class and implement the generate() method.
    Additional methods are provided for accessing results, calculating metrics, and
    exporting data.

    Attributes:
        config: SamplingConfig instance with strategy parameters.
        strategy_name: Name identifier for the sampling strategy.

    Example:
        >>> from ssp import GridSampling, SamplingConfig
        >>> from shapely.geometry import box
        >>> config = SamplingConfig(spacing=100.0, seed=42)
        >>> strategy = GridSampling(config)
        >>> boundary = box(0, 0, 1000, 1000)
        >>> sample_points = strategy.generate(boundary)
        >>> print(f"Generated {len(sample_points)} points")
        >>> strategy.to_geojson("output.geojson")
    """

    def __init__(self, config: SamplingConfig):
        """
        Initialize sampling strategy with configuration.

        Args:
            config: SamplingConfig instance containing strategy parameters.

        Raises:
            TypeError: If config is not a SamplingConfig instance.
        """
        if not isinstance(config, SamplingConfig):
            raise TypeError(
                f"config must be SamplingConfig instance, got {type(config)}"
            )

        self.config: SamplingConfig = config
        self._sample_points: Optional[gpd.GeoDataFrame] = None
        self._generation_timestamp: Optional[datetime] = None
        self.strategy_name: str = self.__class__.__name__

    @abstractmethod
    def generate(self, boundary: Polygon) -> gpd.GeoDataFrame:
        """
        Generate sample points within the given boundary.

        This abstract method must be implemented by all subclasses.
        It should generate spatial sample points according to the specific
        sampling algorithm and return them as a GeoDataFrame.

        Args:
            boundary: Area of interest as shapely Polygon defining the
                      spatial extent for sampling.

        Returns:
            GeoDataFrame with the following structure:
                - geometry: Point geometries (shapely.Point)
                - sample_id: Unique identifier for each point (str)
                - strategy: Name of sampling strategy used (str)
                - timestamp: ISO 8601 timestamp of generation (str)
                - Additional columns specific to the strategy

        Raises:
            ValueError: If boundary is invalid or empty.
            Exception: Subclasses may raise strategy-specific exceptions.

        Example:
            >>> strategy = GridSampling(config)
            >>> points = strategy.generate(boundary)
            >>> assert 'geometry' in points.columns
            >>> assert 'sample_id' in points.columns
        """
        pass

    def _validate_boundary(self, boundary: Polygon) -> None:
        """
        Validate boundary geometry.

        Args:
            boundary: Polygon to validate.

        Raises:
            TypeError: If boundary is not a shapely Polygon.
            BoundaryError: If boundary is invalid or empty.
        """
        if not isinstance(boundary, Polygon):
            raise TypeError(
                f"boundary must be shapely Polygon, got {type(boundary)}"
            )

        if not boundary.is_valid:
            raise BoundaryError(
                "boundary is not a valid polygon. "
                "Check for self-intersections or other geometry errors.",
                details={'is_valid': boundary.is_valid}
            )

        if boundary.is_empty:
            raise BoundaryError(
                "boundary cannot be empty",
                details={'is_empty': boundary.is_empty}
            )

        if boundary.area == 0:
            raise BoundaryError(
                "boundary must have non-zero area",
                details={'area': boundary.area}
            )

    def get_sample_points(self) -> gpd.GeoDataFrame:
        """
        Get the generated sample points.

        Returns:
            GeoDataFrame containing the generated sample points with all
            metadata columns.

        Raises:
            ValueError: If no points have been generated yet. Call generate() first.

        Example:
            >>> strategy = GridSampling(config)
            >>> strategy.generate(boundary)
            >>> points = strategy.get_sample_points()
            >>> print(len(points))
        """
        if self._sample_points is None:
            raise ValueError(
                "No sample points generated yet. "
                "Call generate() method first."
            )

        return self._sample_points

    def get_config(self) -> SamplingConfig:
        """
        Get the sampling configuration.

        Returns:
            SamplingConfig instance containing all strategy parameters.

        Example:
            >>> config = strategy.get_config()
            >>> print(f"Spacing: {config.spacing}m")
        """
        return self.config

    def calculate_coverage_metrics(self) -> Dict[str, Any]:
        """
        Calculate coverage quality metrics for generated sample points.

        This method computes various metrics to assess the quality and
        characteristics of the spatial sampling, including point density,
        coverage area, and spatial extent.

        Returns:
            Dictionary containing the following metrics:
                - n_points: Total number of sample points (int)
                - area_km2: Approximate coverage area in square kilometers (float)
                - density_pts_per_km2: Sampling density (float)
                - bounds: Bounding box [minx, miny, maxx, maxy] (tuple)
                - crs: Coordinate reference system (str)

        Raises:
            SamplingError: If no sample points have been generated yet.

        Example:
            >>> metrics = strategy.calculate_coverage_metrics()
            >>> print(f"Density: {metrics['density_pts_per_km2']} pts/km²")
        """
        if self._sample_points is None:
            raise SamplingError(
                "No sample points generated yet. "
                "Call generate() method first.",
                details={'sample_points': None}
            )

        gdf = self._sample_points

        # Handle empty GeoDataFrame
        if gdf.empty:
            # Use boundary area if available
            area_m2 = 0
            area_km2 = 0
            if self.config.boundary is not None:
                # For geographic coordinates, approximate area
                if self.config.crs == 'EPSG:4326':
                    # Convert degree area to approximate km2
                    from ssp.utils.coordinates import degrees_to_meters
                    minx, miny, maxx, maxy = self.config.boundary.bounds
                    width_deg = maxx - minx
                    height_deg = maxy - miny
                    center_lat = (miny + maxy) / 2

                    # Convert to meters
                    width_m = degrees_to_meters(width_deg, center_lat)
                    height_m = degrees_to_meters(height_deg)
                    area_m2 = width_m * height_m
                else:
                    area_m2 = self.config.boundary.area
                area_km2 = area_m2 / 1e6

            return {
                'n_points': 0,
                'area_km2': round(area_km2, 4),
                'density_pts_per_km2': 0.0,
                'bounds': (0, 0, 0, 0),
                'crs': str(gdf.crs)
            }

        bounds = gdf.total_bounds  # minx, miny, maxx, maxy

        # Validate bounds before creating box
        if len(bounds) != 4:
            raise SamplingError(
                f"Invalid bounds: expected 4 values, got {len(bounds)}",
                details={'bounds': bounds, 'length': len(bounds)}
            )

        # Check for NaN or Inf values
        import numpy as np
        if any(np.isnan(bounds)) or any(np.isinf(bounds)):
            raise SamplingError(
                f"Invalid bounds (NaN/Inf detected): {bounds}",
                details={'bounds': bounds}
            )

        # Calculate approximate area using bounding box
        from shapely.geometry import box
        try:
            bbox = box(bounds[0], bounds[1], bounds[2], bounds[3])

            # For geographic coordinates, convert to approximate area in km2
            if self.config.crs == 'EPSG:4326':
                from ssp.utils.coordinates import degrees_to_meters
                center_lat = (bounds[1] + bounds[3]) / 2
                width_deg = bounds[2] - bounds[0]
                height_deg = bounds[3] - bounds[1]

                # Convert to meters
                width_m = degrees_to_meters(width_deg, center_lat)
                height_m = degrees_to_meters(height_deg)
                area_m2 = width_m * height_m
            else:
                area_m2 = bbox.area

            area_km2 = area_m2 / 1e6
        except Exception as e:
            # Fallback: use convex hull area if box creation fails
            if not gdf.empty and hasattr(gdf, 'unary_union'):
                try:
                    area_m2 = gdf.unary_union.convex_hull.area

                    # For geographic coordinates, approximate area
                    if self.config.crs == 'EPSG:4326':
                        from ssp.utils.coordinates import degrees_to_meters
                        bounds = gdf.total_bounds
                        center_lat = (bounds[1] + bounds[3]) / 2
                        width_deg = bounds[2] - bounds[0]
                        height_deg = bounds[3] - bounds[1]

                        width_m = degrees_to_meters(width_deg, center_lat)
                        height_m = degrees_to_meters(height_deg)
                        area_m2 = width_m * height_m

                    area_km2 = area_m2 / 1e6
                except:
                    # Last resort: use boundary area if available
                    if self.config.boundary is not None:
                        area_m2 = self.config.boundary.area
                        # For geographic coordinates, approximate
                        if self.config.crs == 'EPSG:4326':
                            from ssp.utils.coordinates import degrees_to_meters
                            minx, miny, maxx, maxy = self.config.boundary.bounds
                            width_deg = maxx - minx
                            height_deg = maxy - miny
                            center_lat = (miny + maxy) / 2

                            width_m = degrees_to_meters(width_deg, center_lat)
                            height_m = degrees_to_meters(height_deg)
                            area_m2 = width_m * height_m
                        area_km2 = area_m2 / 1e6
                    else:
                        area_m2 = 0
                        area_km2 = 0
            else:
                area_m2 = 0
                area_km2 = 0

        n_points = len(gdf)
        density = n_points / area_km2 if area_km2 > 0 else 0

        return {
            'n_points': n_points,
            'area_km2': round(area_km2, 4),
            'density_pts_per_km2': round(density, 2),
            'bounds': tuple(bounds),
            'crs': str(gdf.crs)
        }

    def to_geojson(
        self,
        filepath: str,
        include_metadata: bool = True
    ) -> None:
        """
        Save sample points to GeoJSON file.

        Exports the generated sample points to a GeoJSON file with optional
        metadata inclusion. The file can be opened in QGIS, ArcGIS, or any
        GeoJSON-compatible software.

        Args:
            filepath: Output file path (e.g., "sampling_points.geojson")
            include_metadata: If True, adds additional metadata to the
                            FeatureCollection properties.

        Raises:
            ValueError: If no sample points have been generated yet.
            IOError: If filepath cannot be written.

        Example:
            >>> strategy.to_geojson("output.geojson")
            >>> strategy.to_geojson("output_simple.geojson", include_metadata=False)
        """
        if self._sample_points is None:
            raise ValueError(
                "No sample points generated yet. "
                "Call generate() method first."
            )

        try:
            if include_metadata:
                # Add metadata as FeatureCollection properties
                import json
                from geojson import Feature, FeatureCollection, dump

                features = []
                for _, row in self._sample_points.iterrows():
                    feature = Feature(
                        geometry=row['geometry'].__geo_interface__,
                        properties=row.drop('geometry').to_dict()
                    )
                    features.append(feature)

                collection = FeatureCollection(
                    features,
                    properties={
                        'strategy': self.strategy_name,
                        'spacing_m': self.config.spacing,
                        'crs': str(self._sample_points.crs),
                        'seed': self.config.seed,
                        'timestamp': self._generation_timestamp.isoformat() if self._generation_timestamp else None,
                        'n_points': len(self._sample_points)
                    }
                )

                with open(filepath, 'w') as f:
                    dump(collection, f)
            else:
                # Use geopandas built-in export
                self._sample_points.to_file(filepath, driver='GeoJSON')

        except Exception as e:
            raise IOError(f"Failed to write GeoJSON to {filepath}: {e}")

    def __repr__(self) -> str:
        """Return string representation of the sampling strategy."""
        return (
            f"{self.__class__.__name__}("
            f"spacing={self.config.spacing}m, "
            f"crs='{self.config.crs}', "
            f"seed={self.config.seed})"
        )
