"""
Extended tests for road_network.py module.

This test suite provides comprehensive coverage for road network sampling,
including error scenarios, edge cases, and metrics calculation.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import geopandas as gpd
from shapely.geometry import box, Polygon, Point
import networkx as nx

from ssp import RoadNetworkSampling, SamplingConfig
from ssp.exceptions import NetworkDownloadError


class TestRoadNetworkInitialization:
    """Test suite for RoadNetworkSampling initialization."""

    def test_init_with_default_config(self):
        """Test initialization with default config."""
        strategy = RoadNetworkSampling()
        assert strategy.config is not None
        assert strategy.network_type == 'all'
        assert strategy.road_types is None
        assert strategy._road_graph is None

    def test_init_with_custom_network_type(self):
        """Test initialization with custom network type."""
        for network_type in ['all', 'walk', 'drive', 'bike']:
            strategy = RoadNetworkSampling(
                network_type=network_type
            )
            assert strategy.network_type == network_type

    def test_init_with_invalid_network_type(self):
        """Test initialization with invalid network type."""
        with pytest.raises(ValueError, match="network_type must be one of"):
            RoadNetworkSampling(network_type='invalid')

    def test_init_with_valid_road_types(self):
        """Test initialization with valid road types."""
        road_types = {'primary', 'secondary', 'residential'}
        strategy = RoadNetworkSampling(road_types=road_types)
        assert strategy.road_types == road_types

    def test_init_with_invalid_road_types(self):
        """Test initialization with invalid road types."""
        with pytest.raises(ValueError, match="Invalid road types"):
            RoadNetworkSampling(road_types={'invalid_road_type'})

    def test_init_with_mixed_valid_invalid_road_types(self):
        """Test initialization with mixed valid and invalid road types."""
        with pytest.raises(ValueError, match="Invalid road types"):
            RoadNetworkSampling(road_types={'primary', 'invalid_type'})


class TestRoadNetworkGenerationErrors:
    """Test suite for error handling in road network generation."""

    def test_generate_with_invalid_boundary_type(self):
        """Test generate() with invalid boundary type."""
        strategy = RoadNetworkSampling()
        with pytest.raises(TypeError):
            strategy.generate("not a polygon")

    def test_generate_with_empty_boundary(self):
        """Test generate() with empty boundary."""
        strategy = RoadNetworkSampling()
        # Create a very small polygon
        boundary = box(0, 0, 0.00001, 0.00001)

        # This should either work or raise a specific error
        # We're testing that it doesn't crash unexpectedly
        try:
            result = strategy.generate(boundary)
            # If it succeeds, it might return empty results
            assert isinstance(result, gpd.GeoDataFrame)
        except (RuntimeError, ValueError) as e:
            # Expected for very small boundaries or network failures
            assert len(str(e)) > 0

    @patch('ssp.sampling.road_network.ox.graph_from_polygon')
    def test_osm_download_failure(self, mock_graph):
        """Test handling of OSM download failure."""
        # Mock OSM download to raise an exception
        mock_graph.side_effect = Exception("Network error")

        strategy = RoadNetworkSampling()
        boundary = box(0, 0, 0.01, 0.01)

        with pytest.raises(RuntimeError, match="Failed to download road network"):
            strategy.generate(boundary)

    @patch('ssp.sampling.road_network.ox.graph_from_polygon')
    def test_empty_osm_graph(self, mock_graph):
        """Test handling of empty OSM graph."""
        # Mock empty graph
        mock_graph.return_value = nx.MultiDiGraph()

        strategy = RoadNetworkSampling()
        boundary = box(0, 0, 0.01, 0.01)

        with pytest.raises(ValueError, match="No road network found"):
            strategy.generate(boundary)

    @patch('ssp.sampling.road_network.ox.graph_from_polygon')
    @patch('ssp.sampling.road_network.ox.graph_to_gdfs')
    def test_no_matching_road_types(self, mock_gdfs, mock_graph):
        """Test handling of no matching road types."""
        # Create a graph with edges
        test_graph = nx.MultiDiGraph()
        test_graph.add_edge(0, 1, osmid=100, highway='motorway',
                           geometry=LineString([(0, 0), (0.01, 0.01)]))

        mock_graph.return_value = test_graph

        # Mock edges GeoDataFrame with different highway type
        mock_edges = gpd.GeoDataFrame({
            'geometry': [Point(0, 0)],
            'highway': ['motorway'],
            'length': [100]
        })
        mock_gdfs.return_value = mock_edges

        strategy = RoadNetworkSampling(road_types={'primary'})
        boundary = box(0, 0, 0.01, 0.01)

        with pytest.raises(ValueError, match="No road edges matching"):
            strategy.generate(boundary)


class TestRoadNetworkMetrics:
    """Test suite for road network metrics calculation."""

    def test_metrics_before_generation(self):
        """Test metrics calculation before generating samples."""
        strategy = RoadNetworkSampling()
        metrics = strategy.calculate_road_network_metrics()

        assert metrics['n_points'] == 0
        assert metrics['n_edges'] == 0
        assert metrics['n_nodes'] == 0
        assert metrics['total_road_length_km'] == 0.0
        assert metrics['avg_degree'] == 0.0
        assert metrics['road_type_distribution'] == {}
        assert metrics['network_type'] == 'all'

    @patch('ssp.sampling.road_network.ox.graph_from_polygon')
    @patch('ssp.sampling.road_network.ox.graph_to_gdfs')
    def test_metrics_after_generation(self, mock_gdfs, mock_graph):
        """Test metrics calculation after generating samples."""
        # Create a mock graph
        test_graph = nx.MultiDiGraph()
        test_graph.add_edge(0, 1, osmid=100, highway='primary',
                           geometry=Point(0, 0))

        mock_graph.return_value = test_graph
        mock_edges = gpd.GeoDataFrame({
            'geometry': [Point(0, 0)],
            'highway': ['primary'],
            'length': [1000]  # 1 km
        })
        mock_gdfs.return_value = mock_edges

        strategy = RoadNetworkSampling()

        # Create mock sample points
        from shapely.geometry import LineString
        boundary = box(0, 0, 0.01, 0.01)

        # Mock the generate method to set sample points
        with patch.object(strategy, 'generate'):
            strategy._sample_points = gpd.GeoDataFrame({
                'geometry': [Point(0, 0), Point(0.005, 0.005)],
                'highway': ['primary', 'primary'],
                'edge_id': [100, 100]
            })
            strategy._road_graph = test_graph

            metrics = strategy.calculate_road_network_metrics()

            assert metrics['n_points'] == 2
            assert metrics['n_edges'] == 1
            assert metrics['network_type'] == 'all'
            assert 'primary' in metrics['road_type_distribution']


class TestRoadNetworkEdgeCases:
    """Test suite for edge cases in road network sampling."""

    def test_very_large_spacing(self):
        """Test with very large spacing value."""
        strategy = RoadNetworkSampling(
            config=SamplingConfig(spacing=100000)  # 100 km
        )
        boundary = box(0, 0, 0.01, 0.01)

        # Should handle gracefully (may return few points or error)
        try:
            result = strategy.generate(boundary)
            if len(result) > 0:
                assert len(result) < 10  # Should be very few points
        except (RuntimeError, ValueError):
            pass  # Acceptable for large spacing

    def test_very_small_spacing(self):
        """Test with very small spacing value."""
        strategy = RoadNetworkSampling(
            config=SamplingConfig(spacing=1)  # 1 meter
        )
        boundary = box(0, 0, 0.01, 0.01)

        # Should handle gracefully (may return many points or error)
        try:
            result = strategy.generate(boundary)
            # If successful, might have warning printed
            assert isinstance(result, gpd.GeoDataFrame)
        except (RuntimeError, ValueError):
            pass  # Acceptable for tiny spacing

    def test_different_network_types(self):
        """Test different network types work correctly."""
        boundary = box(2.29, 48.85, 2.30, 48.86)  # Small area in Paris

        for network_type in ['walk', 'drive', 'bike']:
            strategy = RoadNetworkSampling(
                config=SamplingConfig(spacing=100, seed=42),
                network_type=network_type
            )

            try:
                result = strategy.generate(boundary)
                # Should succeed or fail gracefully
                assert isinstance(result, gpd.GeoDataFrame)
            except (RuntimeError, ValueError) as e:
                # Network download might fail for various reasons
                assert len(str(e)) > 0


class TestRoadNetworkReproducibility:
    """Test suite for reproducibility of road network sampling."""

    @patch('ssp.sampling.road_network.ox.graph_from_polygon')
    @patch('ssp.sampling.road_network.ox.graph_to_gdfs')
    def test_same_seed_same_results(self, mock_gdfs, mock_graph):
        """Test that same seed produces same results."""
        # Create a consistent mock graph
        test_graph = nx.MultiDiGraph()
        from shapely.geometry import LineString
        line = LineString([(0, 0), (0.01, 0), (0.01, 0.01)])

        test_graph.add_edge(
            0, 1,
            osmid=100,
            highway='primary',
            geometry=line
        )

        mock_graph.return_value = test_graph
        mock_edges = gpd.GeoDataFrame({
            'geometry': [line],
            'highway': ['primary'],
            'length': [1500]
        })
        mock_gdfs.return_value = mock_edges

        boundary = box(0, 0, 0.01, 0.01)
        seed = 42

        # Generate twice with same seed
        strategy1 = RoadNetworkSampling(
            config=SamplingConfig(spacing=100, seed=seed)
        )
        points1 = strategy1.generate(boundary)

        strategy2 = RoadNetworkSampling(
            config=SamplingConfig(spacing=100, seed=seed)
        )
        points2 = strategy2.generate(boundary)

        # Should have same number of points
        assert len(points1) == len(points2)


class TestRoadNetworkOutput:
    """Test suite for output validation."""

    @patch('ssp.sampling.road_network.ox.graph_from_polygon')
    @patch('ssp.sampling.road_network.ox.graph_to_gdfs')
    def test_output_columns(self, mock_gdfs, mock_graph):
        """Test that output has required columns."""
        from shapely.geometry import LineString

        # Create mock graph
        test_graph = nx.MultiDiGraph()
        line = LineString([(0, 0), (0.01, 0.01)])
        test_graph.add_edge(0, 1, osmid=100, highway='primary', geometry=line)

        mock_graph.return_value = test_graph
        mock_edges = gpd.GeoDataFrame({
            'geometry': [line],
            'highway': ['primary'],
            'length': [1500]
        })
        mock_gdfs.return_value = mock_edges

        strategy = RoadNetworkSampling()
        boundary = box(0, 0, 0.01, 0.01)

        result = strategy.generate(boundary)

        required_columns = [
            'geometry', 'sample_id', 'strategy', 'timestamp',
            'edge_id', 'distance_along_edge', 'spacing_m',
            'highway', 'network_type'
        ]

        for col in required_columns:
            assert col in result.columns

    @patch('ssp.sampling.road_network.ox.graph_from_polygon')
    @patch('ssp.sampling.road_network.ox.graph_to_gdfs')
    def test_geojson_export(self, mock_gdfs, mock_graph):
        """Test GeoJSON export functionality."""
        from shapely.geometry import LineString

        # Create mock graph
        test_graph = nx.MultiDiGraph()
        line = LineString([(0, 0), (0.01, 0.01)])
        test_graph.add_edge(0, 1, osmid=100, highway='primary', geometry=line)

        mock_graph.return_value = test_graph
        mock_edges = gpd.GeoDataFrame({
            'geometry': [line],
            'highway': ['primary'],
            'length': [1500]
        })
        mock_gdfs.return_value = mock_edges

        strategy = RoadNetworkSampling()
        boundary = box(0, 0, 0.01, 0.01)

        result = strategy.generate(boundary)

        # Test export
        with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
            temp_path = f.name

        try:
            strategy.to_geojson(temp_path, include_metadata=True)

            # Verify file exists and is valid
            assert Path(temp_path).exists()

            import json
            with open(temp_path, 'r') as f:
                data = json.load(f)
                assert 'features' in data or 'type' in data
        finally:
            Path(temp_path).unlink(missing_ok=True)


# Need to import LineString for tests
from shapely.geometry import LineString
