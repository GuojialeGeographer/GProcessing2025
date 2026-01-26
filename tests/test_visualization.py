"""
Tests for visualization module.

This test suite provides comprehensive coverage for visualization functions,
including strategy comparison, coverage statistics, and spatial distribution plots.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import geopandas as gpd
from shapely.geometry import box, Polygon, Point
import matplotlib.pyplot as plt
import numpy as np

from ssp import GridSampling, SamplingConfig
from ssp.visualization import (
    compare_strategies,
    plot_coverage_statistics,
    plot_spatial_distribution
)


class TestCompareStrategies:
    """Test suite for compare_strategies function."""

    def test_compare_strategies_basic(self):
        """Test basic strategy comparison."""
        boundary = box(0, 0, 1000, 1000)
        strategies = {
            'Grid (100m)': GridSampling(SamplingConfig(spacing=100)),
            'Grid (200m)': GridSampling(SamplingConfig(spacing=200))
        }

        fig = compare_strategies(strategies, boundary)

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_compare_strategies_with_output(self):
        """Test strategy comparison with file output."""
        boundary = box(0, 0, 1000, 1000)
        strategies = {
            'Grid (100m)': GridSampling(SamplingConfig(spacing=100))
        }

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        try:
            fig = compare_strategies(strategies, boundary, output_path=temp_path)
            assert Path(temp_path).exists()
        finally:
            Path(temp_path).unlink(missing_ok=True)
            plt.close('all')

    def test_compare_strategies_empty_dict(self):
        """Test with empty strategies dictionary."""
        boundary = box(0, 0, 1000, 1000)

        with pytest.raises(ValueError, match="strategies dictionary cannot be empty"):
            compare_strategies({}, boundary)

    def test_compare_strategies_invalid_boundary(self):
        """Test with invalid boundary type."""
        strategies = {
            'Grid (100m)': GridSampling(SamplingConfig(spacing=100))
        }

        with pytest.raises(TypeError, match="boundary must be shapely Polygon"):
            compare_strategies(strategies, "not a polygon")

    def test_compare_strategies_all_strategies_fail(self):
        """Test when all strategies fail to generate."""
        boundary = box(0, 0, 0.000001, 0.000001)  # Very small area

        # Create strategies that will fail
        strategies = {
            'Grid (1m)': GridSampling(SamplingConfig(spacing=1, seed=42))
        }

        # Should raise ValueError if all strategies fail
        with pytest.raises(ValueError, match="No strategies generated valid samples"):
            compare_strategies(strategies, boundary)

    def test_compare_strategies_custom_figsize(self):
        """Test with custom figure size."""
        boundary = box(0, 0, 1000, 1000)
        strategies = {
            'Grid (100m)': GridSampling(SamplingConfig(spacing=100))
        }

        fig = compare_strategies(strategies, boundary, figsize=(20, 15))

        assert fig is not None
        assert fig.get_size_inches()[0] == 20
        assert fig.get_size_inches()[1] == 15
        plt.close(fig)

    def test_compare_strategies_multiple_strategies(self):
        """Test comparing multiple strategies."""
        boundary = box(0, 0, 1000, 1000)
        strategies = {
            'Grid (50m)': GridSampling(SamplingConfig(spacing=50)),
            'Grid (100m)': GridSampling(SamplingConfig(spacing=100)),
            'Grid (200m)': GridSampling(SamplingConfig(spacing=200)),
            'Grid (500m)': GridSampling(SamplingConfig(spacing=500))
        }

        fig = compare_strategies(strategies, boundary)

        assert fig is not None
        plt.close(fig)


class TestPlotCoverageStatistics:
    """Test suite for plot_coverage_statistics function."""

    @pytest.fixture
    def sample_points(self):
        """Create sample points for testing."""
        points_data = []
        for i in range(100):
            x = np.random.uniform(0, 1000)
            y = np.random.uniform(0, 1000)
            points_data.append({
                'geometry': Point(x, y),
                'sample_id': f'point_{i}',
                'value': np.random.uniform(0, 100)
            })

        gdf = gpd.GeoDataFrame(points_data, crs='EPSG:4326')
        return gdf

    def test_plot_coverage_statistics_basic(self, sample_points):
        """Test basic coverage statistics plot."""
        fig = plot_coverage_statistics(sample_points)

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_coverage_statistics_with_output(self, sample_points):
        """Test coverage statistics with file output."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        try:
            fig = plot_coverage_statistics(sample_points, output_path=temp_path)
            assert Path(temp_path).exists()
        finally:
            Path(temp_path).unlink(missing_ok=True)
            plt.close('all')

    def test_plot_coverage_statistics_empty_geodataframe(self):
        """Test with empty GeoDataFrame."""
        empty_gdf = gpd.GeoDataFrame(geometry=[])

        with pytest.raises(ValueError, match="points_gdf is empty"):
            plot_coverage_statistics(empty_gdf)

    def test_plot_coverage_statistics_invalid_type(self):
        """Test with invalid input type."""
        with pytest.raises(TypeError, match="points_gdf must be GeoDataFrame"):
            plot_coverage_statistics("not a geodataframe")

    def test_plot_coverage_statistics_no_geometry(self):
        """Test with GeoDataFrame missing geometry column."""
        df = gpd.GeoDataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})

        with pytest.raises(ValueError, match="must contain 'geometry' column"):
            plot_coverage_statistics(df)

    def test_plot_coverage_statistics_single_point(self):
        """Test with single point."""
        gdf = gpd.GeoDataFrame({
            'geometry': [Point(500, 500)]
        })

        fig = plot_coverage_statistics(gdf)
        assert fig is not None
        plt.close(fig)

    def test_plot_coverage_statistics_custom_figsize(self, sample_points):
        """Test with custom figure size."""
        fig = plot_coverage_statistics(sample_points, figsize=(16, 12))

        assert fig is not None
        assert fig.get_size_inches()[0] == 16
        assert fig.get_size_inches()[1] == 12
        plt.close(fig)

    def test_plot_coverage_statistics_large_dataset(self):
        """Test with large dataset."""
        points_data = []
        for i in range(10000):
            x = np.random.uniform(0, 1000)
            y = np.random.uniform(0, 1000)
            points_data.append({
                'geometry': Point(x, y)
            })

        gdf = gpd.GeoDataFrame(points_data, crs='EPSG:4326')

        fig = plot_coverage_statistics(gdf)
        assert fig is not None
        plt.close(fig)


class TestPlotSpatialDistribution:
    """Test suite for plot_spatial_distribution function."""

    @pytest.fixture
    def sample_points(self):
        """Create sample points for testing."""
        points_data = []
        for i in range(50):
            x = np.random.uniform(0, 1000)
            y = np.random.uniform(0, 1000)
            points_data.append({
                'geometry': Point(x, y)
            })

        gdf = gpd.GeoDataFrame(points_data, crs='EPSG:4326')
        return gdf

    def test_plot_spatial_distribution_basic(self, sample_points):
        """Test basic spatial distribution plot."""
        fig = plot_spatial_distribution(sample_points)

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_spatial_distribution_with_boundary(self, sample_points):
        """Test spatial distribution with boundary."""
        boundary = box(0, 0, 1000, 1000)

        fig = plot_spatial_distribution(sample_points, boundary=boundary)

        assert fig is not None
        plt.close(fig)

    def test_plot_spatial_distribution_with_output(self, sample_points):
        """Test spatial distribution with file output."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        try:
            fig = plot_spatial_distribution(
                sample_points,
                output_path=temp_path
            )
            assert Path(temp_path).exists()
        finally:
            Path(temp_path).unlink(missing_ok=True)
            plt.close('all')

    def test_plot_spatial_distribution_custom_title(self, sample_points):
        """Test with custom title."""
        custom_title = "My Custom Distribution Plot"

        fig = plot_spatial_distribution(
            sample_points,
            title=custom_title
        )

        assert fig is not None
        plt.close(fig)

    def test_plot_spatial_distribution_custom_figsize(self, sample_points):
        """Test with custom figure size."""
        fig = plot_spatial_distribution(
            sample_points,
            figsize=(12, 12)
        )

        assert fig is not None
        assert fig.get_size_inches()[0] == 12
        assert fig.get_size_inches()[1] == 12
        plt.close(fig)

    def test_plot_spatial_distribution_single_point(self):
        """Test with single point."""
        gdf = gpd.GeoDataFrame({
            'geometry': [Point(500, 500)]
        })

        fig = plot_spatial_distribution(gdf)
        assert fig is not None
        plt.close(fig)

    def test_plot_spatial_distribution_empty_geodataframe(self):
        """Test with empty GeoDataFrame."""
        empty_gdf = gpd.GeoDataFrame(geometry=[])

        with pytest.raises(ValueError, match="points_gdf is empty"):
            plot_spatial_distribution(empty_gdf)

    def test_plot_spatial_distribution_invalid_type(self):
        """Test with invalid input type."""
        with pytest.raises(TypeError, match="points_gdf must be GeoDataFrame"):
            plot_spatial_distribution("not a geodataframe")

    def test_plot_spatial_distribution_invalid_boundary(self, sample_points):
        """Test with invalid boundary type."""
        fig = plot_spatial_distribution(
            sample_points,
            boundary="not a polygon"
        )
        # Should not raise error, just ignore invalid boundary
        assert fig is not None
        plt.close(fig)


class TestVisualizationEdgeCases:
    """Test suite for edge cases in visualization."""

    def test_compare_strategies_with_same_boundary_multiple_times(self):
        """Test comparing strategies on same boundary multiple times."""
        boundary = box(0, 0, 1000, 1000)
        strategies = {
            'Grid (100m)': GridSampling(SamplingConfig(spacing=100))
        }

        # Run multiple times
        for _ in range(3):
            fig = compare_strategies(strategies, boundary)
            assert fig is not None
            plt.close(fig)

    def test_plot_with_crs_mismatch(self):
        """Test plotting with different CRS."""
        # Create points in one CRS
        points_data = []
        for i in range(20):
            x = np.random.uniform(0, 1000)
            y = np.random.uniform(0, 1000)
            points_data.append({
                'geometry': Point(x, y)
            })

        gdf = gpd.GeoDataFrame(points_data, crs='EPSG:3857')

        fig = plot_coverage_statistics(gdf)
        assert fig is not None
        plt.close(fig)

    def test_plot_with_missing_crs(self):
        """Test plotting with missing CRS information."""
        points_data = []
        for i in range(20):
            x = np.random.uniform(0, 1000)
            y = np.random.uniform(0, 1000)
            points_data.append({
                'geometry': Point(x, y)
            })

        gdf = gpd.GeoDataFrame(points_data)  # No CRS specified

        fig = plot_coverage_statistics(gdf)
        assert fig is not None
        plt.close(fig)

    def test_plot_points_exactly_same_location(self):
        """Test plotting with points at exactly same location."""
        points_data = []
        for i in range(10):
            points_data.append({
                'geometry': Point(500, 500)  # All same location
            })

        gdf = gpd.GeoDataFrame(points_data, crs='EPSG:4326')

        fig = plot_coverage_statistics(gdf)
        assert fig is not None
        plt.close(fig)

    def test_plot_with_extreme_values(self):
        """Test plotting with extreme coordinate values."""
        points_data = []
        for i in range(20):
            x = np.random.uniform(-180, 180)  # Longitude range
            y = np.random.uniform(-90, 90)    # Latitude range
            points_data.append({
                'geometry': Point(x, y)
            })

        gdf = gpd.GeoDataFrame(points_data, crs='EPSG:4326')

        fig = plot_coverage_statistics(gdf)
        assert fig is not None
        plt.close(fig)


class TestVisualizationIntegration:
    """Integration tests for visualization functions."""

    def test_full_workflow_visualization(self):
        """Test complete workflow: generate samples -> visualize."""
        boundary = box(0, 0, 1000, 1000)

        # Generate samples
        strategy = GridSampling(SamplingConfig(spacing=100))
        points = strategy.generate(boundary)

        # Test all visualization functions
        fig1 = plot_coverage_statistics(points)
        assert fig1 is not None
        plt.close(fig1)

        fig2 = plot_spatial_distribution(points, boundary=boundary)
        assert fig2 is not None
        plt.close(fig2)

        strategies = {
            'Grid (100m)': strategy
        }
        fig3 = compare_strategies(strategies, boundary)
        assert fig3 is not None
        plt.close(fig3)

    def test_visualization_with_multiple_boundaries(self):
        """Test visualizations with different boundary types."""
        boundaries = [
            box(0, 0, 1000, 1000),
            box(100, 100, 900, 900),
            box(500, 500, 600, 600)
        ]

        for boundary in boundaries:
            strategy = GridSampling(SamplingConfig(spacing=100))
            points = strategy.generate(boundary)

            if len(points) > 0:
                fig = plot_spatial_distribution(points, boundary=boundary)
                assert fig is not None
                plt.close(fig)
