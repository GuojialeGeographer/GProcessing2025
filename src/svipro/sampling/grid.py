"""
Grid Sampling Strategy Module

Implements regular grid-based sampling for spatial point generation.
This is the simplest and most transparent sampling method, ideal for
baseline measurements and comparative studies.

Grid sampling provides:
- Uniform spatial coverage
- Complete reproducibility (same parameters = same results)
- Easy to understand and validate
- Fast computation
"""

from datetime import datetime
from typing import Optional
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon

from svipro.sampling.base import SamplingStrategy, SamplingConfig


class GridSampling(SamplingStrategy):
    """
    Regular grid sampling strategy.

    Creates sample points at regular intervals within the area of interest.
    This is the most transparent and reproducible sampling method.

    Example:
        >>> from shapely.geometry import box
        >>> boundary = box(0, 0, 1000, 1000)  # 1km x 1km area
        >>> config = SamplingConfig(spacing=100)  # 100m spacing
        >>> strategy = GridSampling(config)
        >>> points = strategy.generate(boundary)
        >>> print(f"Generated {len(points)} sample points")
    """

    def __init__(self, config: Optional[SamplingConfig] = None):
        """
        Initialize grid sampling strategy.

        Args:
            config: SamplingConfig instance. If None, uses defaults.
        """
        if config is None:
            config = SamplingConfig()
        super().__init__(config)
        self.strategy_name = "grid_sampling"

    def generate(self, boundary: Polygon) -> gpd.GeoDataFrame:
        """
        Generate grid sample points within boundary.

        Creates a regular grid of sample points with the specified spacing.
        Points are generated at the intersection of grid lines, and only
        points that fall within the boundary are retained.

        Args:
            boundary: Area of interest as shapely Polygon

        Returns:
            GeoDataFrame with grid sample points containing:
                - geometry: Point geometries
                - sample_id: Unique identifier
                - strategy: Strategy name
                - timestamp: Generation timestamp
                - grid_x, grid_y: Grid indices
                - spacing_m: Spacing used

        Raises:
            ValueError: If boundary is invalid
        """
        # Validate boundary
        self._validate_boundary(boundary)

        # Store boundary and timestamp
        self.config.boundary = boundary
        self._generation_timestamp = datetime.now()

        # Get boundary bounds
        minx, miny, maxx, maxy = boundary.bounds

        # Calculate number of points in each direction
        x_coords = np.arange(minx, maxx + self.config.spacing, self.config.spacing)
        y_coords = np.arange(miny, maxy + self.config.spacing, self.config.spacing)

        # Create grid points
        points = []
        for i, x in enumerate(x_coords):
            for j, y in enumerate(y_coords):
                point = Point(x, y)
                # Only keep points within boundary
                if boundary.contains(point):
                    points.append({
                        'geometry': point,
                        'sample_id': f"{self.strategy_name}_{i:04d}_{j:04d}",
                        'strategy': self.strategy_name,
                        'timestamp': self._generation_timestamp.isoformat(),
                        'grid_x': i,
                        'grid_y': j,
                        'spacing_m': self.config.spacing,
                    })

        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(points, crs=self.config.crs)
        self._sample_points = gdf

        return gdf

    def optimize_spacing_for_target_n(
        self,
        boundary: Polygon,
        target_n: int,
        min_spacing: float = 10.0,
        max_spacing: float = 1000.0
    ) -> gpd.GeoDataFrame:
        """
        Find optimal spacing to achieve target number of points.

        Uses binary search to find spacing that yields approximately
        the target number of sample points.

        Args:
            boundary: Area of interest
            target_n: Desired number of sample points
            min_spacing: Minimum spacing in meters
            max_spacing: Maximum spacing in meters

        Returns:
            GeoDataFrame with optimized grid sampling
        """
        # Binary search for optimal spacing
        low, high = min_spacing, max_spacing
        best_gdf = None
        best_diff = float('inf')

        for _ in range(20):  # 20 iterations is sufficient
            mid_spacing = (low + high) / 2
            self.config.spacing = mid_spacing
            gdf = self.generate(boundary)
            diff = abs(len(gdf) - target_n)

            if diff < best_diff:
                best_diff = diff
                best_gdf = gdf

            if len(gdf) < target_n:
                high = mid_spacing
            else:
                low = mid_spacing

        self._sample_points = best_gdf
        return best_gdf
