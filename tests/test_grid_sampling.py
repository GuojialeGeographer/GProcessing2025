"""
Unit tests for GridSampling strategy.

Tests for grid-based spatial sampling including reproducibility,
boundary filtering, and edge cases.
"""

from datetime import datetime
import pytest
import numpy as np
import geopandas as gpd
from shapely.geometry import box, Polygon, Point

from ssp import GridSampling, SamplingConfig


class TestGridSamplingInitialization:
    """Test suite for GridSampling initialization."""

    def test_default_initialization(self):
        """Test initialization with default config."""
        strategy = GridSampling()

        assert strategy.config.spacing == 100.0
        assert strategy.strategy_name == "grid_sampling"
        assert strategy._sample_points is None

    def test_custom_initialization(self):
        """Test initialization with custom config."""
        config = SamplingConfig(spacing=50.0, seed=123)
        strategy = GridSampling(config)

        assert strategy.config.spacing == 50.0
        assert strategy.config.seed == 123

    def test_none_config_creates_default(self):
        """Test that None config creates default config."""
        strategy = GridSampling(config=None)

        assert isinstance(strategy.config, SamplingConfig)


class TestGridSamplingGenerate:
    """Test suite for GridSampling.generate() method."""

    @pytest.fixture
    def simple_box_boundary(self):
        """Create a simple square boundary for testing."""
        return box(0, 0, 1000, 1000)

    @pytest.fixture
    def rectangular_boundary(self):
        """Create a rectangular boundary."""
        return box(0, 0, 2000, 1000)

    @pytest.fixture
    def complex_boundary(self):
        """Create a more complex polygon boundary."""
        # Create an L-shaped polygon
        coords = [
            (0, 0), (1000, 0), (1000, 500),
            (500, 500), (500, 1000), (0, 1000), (0, 0)
        ]
        return Polygon(coords)

    def test_generate_returns_geodataframe(self, simple_box_boundary):
        """Test that generate returns GeoDataFrame."""
        strategy = GridSampling(SamplingConfig(spacing=100))
        result = strategy.generate(simple_box_boundary)

        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) > 0

    def test_generate_has_required_columns(self, simple_box_boundary):
        """Test that generated GeoDataFrame has required columns."""
        strategy = GridSampling(SamplingConfig(spacing=100))
        result = strategy.generate(simple_box_boundary)

        required_columns = [
            'geometry', 'sample_id', 'strategy', 'timestamp',
            'grid_x', 'grid_y', 'spacing_m'
        ]

        for col in required_columns:
            assert col in result.columns

    def test_generate_with_100m_spacing(self, simple_box_boundary):
        """Test grid generation with 100m spacing."""
        # Use projected CRS for accurate meter-based spacing
        strategy = GridSampling(SamplingConfig(spacing=100.0, crs="EPSG:3857"))
        result = strategy.generate(simple_box_boundary)

        # Should generate points with 100m spacing
        assert len(result) > 0
        # Check spacing is correct
        assert result['spacing_m'].iloc[0] == 100.0

    def test_generate_with_50m_spacing(self, simple_box_boundary):
        """Test grid generation with 50m spacing."""
        strategy = GridSampling(SamplingConfig(spacing=50.0, crs="EPSG:3857"))
        result = strategy.generate(simple_box_boundary)

        # 50m spacing should generate more points than 100m
        assert len(result) > 0
        assert result['spacing_m'].iloc[0] == 50.0

    def test_generate_with_200m_spacing(self, simple_box_boundary):
        """Test grid generation with 200m spacing."""
        strategy = GridSampling(SamplingConfig(spacing=200.0, crs="EPSG:3857"))
        result = strategy.generate(simple_box_boundary)

        # 200m spacing should generate fewer points
        assert len(result) > 0
        assert result['spacing_m'].iloc[0] == 200.0

    def test_generate_filters_boundary_points(self, complex_boundary):
        """Test that only points within boundary are included."""
        strategy = GridSampling(SamplingConfig(spacing=100))
        result = strategy.generate(complex_boundary)

        # Check that all points are within boundary
        for point in result.geometry:
            assert complex_boundary.contains(point)

    def test_generate_empty_geodataframe_for_small_boundary(self):
        """Test generation with very small boundary that contains no grid points."""
        # Create a tiny triangle that's smaller than grid spacing
        tiny_triangle = Polygon([(0, 0), (1, 0), (0, 1)])
        strategy = GridSampling(SamplingConfig(spacing=100))

        result = strategy.generate(tiny_triangle)

        # Should return GeoDataFrame even if empty
        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 0

    def test_generate_with_invalid_boundary_raises_error(self):
        """Test that invalid boundary type raises appropriate error."""
        strategy = GridSampling()
        invalid_boundary = "not a polygon"

        with pytest.raises(TypeError) as excinfo:
            strategy.generate(invalid_boundary)

        assert "Polygon" in str(excinfo.value)

    def test_sample_id_format(self, simple_box_boundary):
        """Test that sample IDs follow correct format."""
        strategy = GridSampling(SamplingConfig(spacing=100, crs="EPSG:3857"))
        result = strategy.generate(simple_box_boundary)

        # Check sample ID format
        first_id = result['sample_id'].iloc[0]
        assert "grid_sampling" in first_id
        assert '_' in first_id  # Should have underscores

    def test_grid_indices_correct(self, simple_box_boundary):
        """Test that grid_x and grid_y indices start from 0."""
        strategy = GridSampling(SamplingConfig(spacing=100, crs="EPSG:3857"))
        result = strategy.generate(simple_box_boundary)

        # Check that indices start from 0
        min_grid_x = result['grid_x'].min()
        min_grid_y = result['grid_y'].min()
        assert min_grid_x >= 0
        assert min_grid_y >= 0

    def test_spacing_recorded_correctly(self, simple_box_boundary):
        """Test that spacing_m column records correct spacing."""
        strategy = GridSampling(SamplingConfig(spacing=75.5))
        result = strategy.generate(simple_box_boundary)

        assert all(result['spacing_m'] == 75.5)

    def test_timestamp_included(self, simple_box_boundary):
        """Test that timestamp is included and valid."""
        strategy = GridSampling(SamplingConfig(spacing=100))
        result = strategy.generate(simple_box_boundary)

        # Check timestamp is present and valid ISO format
        assert 'timestamp' in result.columns
        timestamp_str = result['timestamp'].iloc[0]

        # Should be able to parse as ISO datetime
        datetime.fromisoformat(timestamp_str)

    def test_crs_preserved(self, simple_box_boundary):
        """Test that CRS from config is preserved."""
        config = SamplingConfig(spacing=100, crs="EPSG:3857")
        strategy = GridSampling(config)
        result = strategy.generate(simple_box_boundary)

        assert str(result.crs) == "EPSG:3857"


class TestGridSamplingReproducibility:
    """Test suite for reproducibility with seed parameter."""

    @pytest.fixture
    def test_boundary(self):
        """Create test boundary."""
        return box(0, 0, 500, 500)

    def test_same_seed_produces_same_results(self, test_boundary):
        """Test that identical config produces identical results."""
        config = SamplingConfig(spacing=50, seed=42, crs="EPSG:3857")

        # Generate first time
        strategy1 = GridSampling(config)
        points1 = strategy1.generate(test_boundary)

        # Generate second time with same config
        strategy2 = GridSampling(config)
        points2 = strategy2.generate(test_boundary)

        # Should have same number of points
        assert len(points1) == len(points2)

        # Compare geometries and other columns (exclude timestamp)
        cols_to_compare = ['geometry', 'sample_id', 'strategy', 'grid_x', 'grid_y', 'spacing_m']
        points1_subset = points1[cols_to_compare]
        points2_subset = points2[cols_to_compare]

        assert points1_subset.equals(points2_subset)

    def test_different_seeds_produce_same_results(self, test_boundary):
        """Test that different seeds produce same results (grid is deterministic)."""
        config1 = SamplingConfig(spacing=50, seed=42, crs="EPSG:3857")
        config2 = SamplingConfig(spacing=50, seed=999, crs="EPSG:3857")

        strategy1 = GridSampling(config1)
        strategy2 = GridSampling(config2)

        points1 = strategy1.generate(test_boundary)
        points2 = strategy2.generate(test_boundary)

        # Grid sampling is deterministic, so seed shouldn't affect it
        cols_to_compare = ['geometry', 'grid_x', 'grid_y', 'spacing_m']
        points1_subset = points1[cols_to_compare]
        points2_subset = points2[cols_to_compare]

        assert points1_subset.equals(points2_subset)

    def test_reproducibility_across_multiple_runs(self, test_boundary):
        """Test reproducibility across multiple generation calls."""
        config = SamplingConfig(spacing=75, seed=123, crs="EPSG:3857")

        results = []
        for _ in range(3):
            # Create new instance each time to ensure independence
            strategy = GridSampling(config)
            points = strategy.generate(test_boundary)
            results.append(points)

        # All results should have same number of points
        assert len(results[0]) == len(results[1]) == len(results[2])

        # Compare spatial attributes (exclude timestamp)
        cols_to_compare = ['geometry', 'grid_x', 'grid_y', 'spacing_m']
        for i in range(1, len(results)):
            assert results[0][cols_to_compare].equals(results[i][cols_to_compare])


class TestGridSamplingEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_zero_spacing_raises_error(self):
        """Test that zero spacing raises configuration error."""
        with pytest.raises(ValueError) as excinfo:
            GridSampling(SamplingConfig(spacing=0))

        assert "spacing" in str(excinfo.value).lower()

    def test_negative_spacing_raises_error(self):
        """Test that negative spacing raises configuration error."""
        with pytest.raises(ValueError) as excinfo:
            GridSampling(SamplingConfig(spacing=-50))

        assert "spacing" in str(excinfo.value).lower()

    def test_very_small_spacing(self):
        """Test with very small spacing (1 meter)."""
        boundary = box(0, 0, 100, 100)  # Small area in projected CRS
        strategy = GridSampling(SamplingConfig(spacing=1.0, crs="EPSG:3857"))
        result = strategy.generate(boundary)

        # Should generate many points (at least 5000 in 100x100m area)
        assert len(result) > 5000

    def test_very_large_spacing(self):
        """Test with very large spacing."""
        boundary = box(0, 0, 1000, 1000)
        strategy = GridSampling(SamplingConfig(spacing=2000))
        result = strategy.generate(boundary)

        # Should generate few points (maybe just 1)
        assert len(result) <= 4


class TestGridSamplingOptimizeSpacing:
    """Test suite for optimize_spacing_for_target_n method."""

    @pytest.fixture
    def test_boundary(self):
        return box(0, 0, 1000, 1000)

    def test_optimize_for_target_n(self, test_boundary):
        """Test optimizing spacing for target number of points."""
        strategy = GridSampling(SamplingConfig(spacing=100))

        # Target approximately 50 points
        result = strategy.optimize_spacing_for_target_n(
            test_boundary, target_n=50, min_spacing=20, max_spacing=200
        )

        # Should be close to 50 points (within 20%)
        assert 40 <= len(result) <= 60

    def test_optimize_modifies_config_spacing(self, test_boundary):
        """Test that optimization modifies config spacing."""
        original_spacing = 100.0
        strategy = GridSampling(SamplingConfig(spacing=original_spacing))

        strategy.optimize_spacing_for_target_n(
            test_boundary, target_n=30, min_spacing=50, max_spacing=150
        )

        # Spacing should have changed
        assert strategy.config.spacing != original_spacing

    def test_optimize_with_zero_target_raises_error(self, test_boundary):
        """Test that zero target_n raises error."""
        strategy = GridSampling()

        with pytest.raises(ValueError) as excinfo:
            strategy.optimize_spacing_for_target_n(test_boundary, target_n=0)

        assert "target_n must be positive" in str(excinfo.value)

    def test_optimize_with_negative_target_raises_error(self, test_boundary):
        """Test that negative target_n raises error."""
        strategy = GridSampling()

        with pytest.raises(ValueError) as excinfo:
            strategy.optimize_spacing_for_target_n(test_boundary, target_n=-10)

        assert "target_n must be positive" in str(excinfo.value)

    def test_optimize_with_invalid_range_raises_error(self, test_boundary):
        """Test that invalid spacing range raises error."""
        strategy = GridSampling()

        with pytest.raises(ValueError) as excinfo:
            strategy.optimize_spacing_for_target_n(
                test_boundary, target_n=50, min_spacing=100, max_spacing=50
            )

        assert "min_spacing must be less than max_spacing" in str(excinfo.value)


class TestGridSamplingPerformance:
    """Test suite for performance characteristics."""

    def test_large_boundary_performance(self):
        """Test that large boundaries are handled efficiently."""
        # 10km x 10km area with 100m spacing
        large_boundary = box(0, 0, 10000, 10000)
        strategy = GridSampling(SamplingConfig(spacing=100))

        # Should complete in reasonable time
        result = strategy.generate(large_boundary)

        # Should generate around 10,000 points
        assert len(result) > 9000
        assert len(result) < 11000

    def test_performance_with_many_small_boundaries(self):
        """Test performance when generating many small grids."""
        small_boundary = box(0, 0, 100, 100)
        spacing = 10

        # Generate multiple times and verify consistency
        results = []
        for _ in range(10):
            strategy = GridSampling(SamplingConfig(spacing=spacing, crs="EPSG:3857"))
            result = strategy.generate(small_boundary)
            results.append(len(result))

        # All generations should produce same number of points
        assert len(set(results)) == 1  # All values identical

        # Should generate reasonable number of points for 100x100m area with 10m spacing
        expected_points = results[0]
        assert expected_points > 50  # At minimum 50 points
        assert expected_points < 200  # At most 200 points


class TestGridSamplingIntegration:
    """Integration tests for GridSampling with other components."""

    def test_generate_and_export_workflow(self):
        """Test complete workflow: generate -> export -> verify."""
        import tempfile
        import os

        boundary = box(0, 0, 500, 500)
        strategy = GridSampling(SamplingConfig(spacing=50, seed=42))

        # Generate
        points = strategy.generate(boundary)

        # Export to GeoJSON
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "test_output.geojson")
            strategy.to_geojson(output_file)

            # Verify file exists
            assert os.path.exists(output_file)

            # Verify can be read back
            imported = gpd.read_file(output_file)
            assert len(imported) == len(points)

    def test_generate_and_calculate_metrics(self):
        """Test workflow: generate -> calculate metrics."""
        boundary = box(0, 0, 1000, 1000)
        strategy = GridSampling(SamplingConfig(spacing=100))

        points = strategy.generate(boundary)
        metrics = strategy.calculate_coverage_metrics()

        # Verify metrics are reasonable
        assert metrics['n_points'] == len(points)
        assert 'area_km2' in metrics
        assert 'density_pts_per_km2' in metrics
        assert 'bounds' in metrics
        assert 'crs' in metrics
