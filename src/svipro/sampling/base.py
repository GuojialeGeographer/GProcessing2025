"""
Base Sampling Strategy Class

Defines the abstract interface for all sampling strategies.
Ensures reproducibility and standardization across different methods.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import geopandas as gpd
from shapely.geometry import Point, Polygon


@dataclass
class SamplingConfig:
    """
    Configuration for sampling strategy.

    Attributes:
        spacing: Distance between sample points (meters)
        crs: Coordinate Reference System (EPSG code)
        seed: Random seed for reproducibility
        boundary: Area of interest as shapely Polygon
        metadata: Additional metadata dictionary
    """
    spacing: float = 100.0
    crs: str = "EPSG:4326"
    seed: int = 42
    boundary: Optional[Polygon] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization."""
        return {
            'spacing': self.spacing,
            'crs': self.crs,
            'seed': self.seed,
            'boundary': self.boundary.wkt if self.boundary else None,
            'metadata': self.metadata
        }


class SamplingStrategy(ABC):
    """
    Abstract base class for sampling strategies.

    All sampling strategies must inherit from this class and implement
    the generate() method. This ensures consistent interface and
    reproducibility across different sampling methods.

    Example:
        >>> strategy = GridSampling(config)
        >>> sample_points = strategy.generate(boundary)
        >>> strategy.save_metadata('sampling_protocol.yaml')
    """

    def __init__(self, config: SamplingConfig):
        """
        Initialize sampling strategy.

        Args:
            config: SamplingConfig instance with parameters
        """
        self.config = config
        self._sample_points: Optional[gpd.GeoDataFrame] = None

    @abstractmethod
    def generate(self, boundary: Polygon) -> gpd.GeoDataFrame:
        """
        Generate sample points within the given boundary.

        Args:
            boundary: Area of interest as shapely Polygon

        Returns:
            GeoDataFrame with Point geometries and metadata columns:
                - geometry: Point geometries
                - sample_id: Unique identifier for each point
                - strategy: Name of sampling strategy used
                - [additional columns specific to strategy]
        """
        pass

    def get_sample_points(self) -> gpd.GeoDataFrame:
        """Get the generated sample points."""
        if self._sample_points is None:
            raise ValueError("No sample points generated yet. Call generate() first.")
        return self._sample_points

    def get_config(self) -> SamplingConfig:
        """Get the sampling configuration."""
        return self.config

    def calculate_coverage_metrics(self) -> Dict[str, float]:
        """
        Calculate coverage quality metrics.

        Returns:
            Dictionary with metrics:
                - n_points: Total number of sample points
                - area_km2: Coverage area in square kilometers
                - density: Points per square kilometer
                - avg_spacing: Average distance to nearest neighbor
        """
        if self._sample_points is None:
            raise ValueError("No sample points generated yet.")

        gdf = self._sample_points
        bounds = gdf.total_bounds  # minx, miny, maxx, maxy

        # Calculate approximate area
        from shapely.geometry import box
        area_m2 = box(*bounds).area
        area_km2 = area_m2 / 1e6

        n_points = len(gdf)
        density = n_points / area_km2

        return {
            'n_points': n_points,
            'area_km2': round(area_km2, 2),
            'density_pts_per_km2': round(density, 2),
        }

    def to_geojson(self, filepath: str) -> None:
        """
        Save sample points to GeoJSON file.

        Args:
            filepath: Output file path
        """
        if self._sample_points is None:
            raise ValueError("No sample points generated yet.")
        self._sample_points.to_file(filepath, driver='GeoJSON')

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(spacing={self.config.spacing}m)"
