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

Features:
- Deterministic grid generation
- Configurable spacing and alignment
- Boundary-aware point filtering
- Seed-based reproducibility
- Automatic coordinate conversion for geographic CRS
"""

from datetime import datetime
from typing import Optional, Tuple
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon

from ssp.sampling.base import SamplingStrategy, SamplingConfig
from ssp.utils.coordinates import convert_spacing_for_crs


class GridSampling(SamplingStrategy):
    """
    Regular grid sampling strategy.

    Creates sample points at regular intervals within the area of interest.
    This is the most transparent and reproducible sampling method.

    The grid is aligned with the coordinate system axes, starting from the
    minimum coordinates of the boundary. Points are only included if they
    fall within the boundary polygon.

    Attributes:
        strategy_name: Identifier for this sampling strategy
        config: SamplingConfig with spacing and other parameters

    Example:
        >>> from shapely.geometry import box
        >>> boundary = box(0, 0, 1000, 1000)  # 1km x 1km area
        >>> config = SamplingConfig(spacing=100, seed=42)  # 100m spacing
        >>> strategy = GridSampling(config)
        >>> points = strategy.generate(boundary)
        >>> print(f"Generated {len(points)} sample points")
        >>> # Same configuration will produce identical results
        >>> strategy2 = GridSampling(config)
        >>> points2 = strategy2.generate(boundary)
        >>> assert points.equals(points2)  # Reproducible!
    """

    def __init__(self, config: Optional[SamplingConfig] = None):
        """
        Initialize grid sampling strategy.

        Args:
            config: SamplingConfig instance. If None, uses defaults.

        Raises:
            TypeError: If config is not None and not a SamplingConfig.
        """
        if config is None:
            config = SamplingConfig()

        super().__init__(config)
        self.strategy_name = "grid_sampling"

    def generate(self, boundary: Polygon) -> gpd.GeoDataFrame:
        """
        Generate grid sample points within boundary.

        Creates a regular grid of sample points with the specified spacing.
        Points are generated at the intersection of grid lines aligned with
        the coordinate system axes. Only points within the boundary are retained.

        The grid is deterministic and reproducible given the same boundary and
        configuration (spacing, seed, etc.).

        Args:
            boundary: Area of interest as shapely Polygon. Must be a valid,
                      non-empty polygon with non-zero area.

        Returns:
            GeoDataFrame with grid sample points containing:
                - geometry: Point geometries (shapely.Point)
                - sample_id: Unique identifier (str, format: "grid_sampling_XXXX_YYYY")
                - strategy: Strategy name ("grid_sampling")
                - timestamp: Generation timestamp (ISO 8601 string)
                - grid_x: X-coordinate index in grid (int)
                - grid_y: Y-coordinate index in grid (int)
                - spacing_m: Spacing used in meters (float)

        Raises:
            ValueError: If boundary is invalid, empty, or has zero area.
            TypeError: If boundary is not a shapely Polygon.

        Note:
            Grid alignment starts from the minimum x and y coordinates of
            the boundary. This ensures consistent grid positioning across
            different calls with the same boundary.

        Example:
            >>> strategy = GridSampling(SamplingConfig(spacing=50))
            >>> points = strategy.generate(boundary)
            >>> assert len(points) > 0
            >>> assert 'grid_x' in points.columns
            >>> assert 'grid_y' in points.columns
        """
        # Validate boundary
        self._validate_boundary(boundary)

        # Store boundary and timestamp
        self.config.boundary = boundary
        self._generation_timestamp = datetime.now()

        # Set random seed for reproducibility
        # Although grid generation is deterministic, this ensures
        # consistency if any stochastic operations are added
        np.random.seed(self.config.seed)

        # Get boundary bounds
        minx, miny, maxx, maxy = boundary.bounds

        # Convert spacing from meters to appropriate units for the CRS
        # For EPSG:4326 (geographic), this converts meters to degrees
        # For projected coordinate systems (meters), it returns the same value
        actual_spacing = convert_spacing_for_crs(
            self.config.spacing,
            self.config.crs,
            boundary
        )

        # Calculate grid coordinates
        # Use arange with careful endpoint handling to ensure consistent coverage
        x_coords = np.arange(minx, maxx + actual_spacing, actual_spacing)
        y_coords = np.arange(miny, maxy + actual_spacing, actual_spacing)

        # Pre-allocate list for better performance
        points = []
        total_potential = len(x_coords) * len(y_coords)

        # Generate grid points
        for i, x in enumerate(x_coords):
            for j, y in enumerate(y_coords):
                point = Point(x, y)

                # Only keep points within boundary (spatial filter)
                # Using contains() is more accurate than intersects()
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
        if points:
            gdf = gpd.GeoDataFrame(points, crs=self.config.crs)
        else:
            # Return empty GeoDataFrame if no points in boundary
            gdf = gpd.GeoDataFrame(columns=[
                'geometry', 'sample_id', 'strategy', 'timestamp',
                'grid_x', 'grid_y', 'spacing_m'
            ], crs=self.config.crs)

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

        Uses binary search to find the spacing that yields approximately
        the target number of sample points. This is useful when you need
        a specific sample size for statistical requirements or budget constraints.

        The method modifies the config.spacing attribute to the optimal value.

        Args:
            boundary: Area of interest as shapely Polygon
            target_n: Desired number of sample points (must be positive)
            min_spacing: Minimum spacing in meters (default: 10.0)
            max_spacing: Maximum spacing in meters (default: 1000.0)

        Returns:
            GeoDataFrame with optimized grid sampling that has approximately
            target_n points. The actual number may differ slightly due to
            boundary geometry and grid alignment.

        Raises:
            ValueError: If target_n is not positive
            ValueError: If min_spacing >= max_spacing
            ValueError: If boundary is invalid

        Note:
            This method modifies the config.spacing attribute. The original
            spacing value will be lost. If you need to preserve it, create a
            new GridSampling instance or copy the config first.

        Example:
            >>> strategy = GridSampling(SamplingConfig(spacing=100))
            >>> # Want approximately 500 points
            >>> points = strategy.optimize_spacing_for_target_n(
            ...     boundary, target_n=500, min_spacing=20, max_spacing=200
            ... )
            >>> print(f"Generated {len(points)} points")
            >>> print(f"Optimal spacing: {strategy.config.spacing}m")
        """
        # Validate inputs
        if target_n <= 0:
            raise ValueError(f"target_n must be positive (got {target_n})")

        if min_spacing >= max_spacing:
            raise ValueError(
                f"min_spacing must be less than max_spacing "
                f"(got {min_spacing} >= {max_spacing})"
            )

        # Validate boundary
        self._validate_boundary(boundary)

        # Estimate area to check if target_n is achievable
        from ssp.utils.coordinates import convert_spacing_for_crs

        # Convert min_spacing to estimate maximum possible points
        min_actual_spacing = convert_spacing_for_crs(min_spacing, self.config.crs, boundary)
        minx, miny, maxx, maxy = boundary.bounds

        # Estimate maximum number of points with min spacing (densest possible)
        x_max_count = int((maxx - minx) / min_actual_spacing) + 1
        y_max_count = int((maxy - miny) / min_actual_spacing) + 1
        max_possible_points = x_max_count * y_max_count

        if target_n > max_possible_points:
            raise ValueError(
                f"Target point count {target_n} is too high for the boundary area. "
                f"Maximum achievable with {min_spacing}m spacing: ~{max_possible_points} points. "
                f"Use a larger boundary or reduce target_n to <= {max_possible_points}."
            )

        # Binary search for optimal spacing
        low, high = min_spacing, max_spacing
        best_gdf = None
        best_diff = float('inf')
        original_spacing = self.config.spacing

        # Perform binary search (20 iterations is sufficient for meter precision)
        for iteration in range(20):
            mid_spacing = (low + high) / 2
            self.config.spacing = mid_spacing
            gdf = self.generate(boundary)
            diff = abs(len(gdf) - target_n)

            if diff < best_diff:
                best_diff = diff
                best_gdf = gdf

            # Adjust search range
            if len(gdf) < target_n:
                high = mid_spacing  # Need smaller spacing (more points)
            else:
                low = mid_spacing  # Need larger spacing (fewer points)

            # Early exit if perfect match
            if diff == 0:
                break

        # Restore original spacing if needed, or keep optimal
        # For now, we keep the optimal spacing
        self._sample_points = best_gdf

        return best_gdf
