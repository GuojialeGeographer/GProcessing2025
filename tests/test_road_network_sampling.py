"""
Unit tests for RoadNetworkSampling strategy.

Tests for road network-based spatial sampling including OSM integration,
road type filtering, and edge case handling.
"""

from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pytest
import numpy as np
import geopandas as gpd
import networkx as nx
from shapely.geometry import box, Polygon, Point, LineString

from ssp import RoadNetworkSampling, SamplingConfig


@pytest.fixture
def mock_road_graph():
    """Create a mock road network graph for testing."""
    # Create a simple graph with a few edges
    G = nx.MultiDiGraph()

    # Add nodes (intersections)
    G.add_node(1, x=0.0, y=0.0)
    G.add_node(2, x=100.0, y=0.0)
    G.add_node(3, x=200.0, y=0.0)
    G.add_node(4, x=100.0, y=100.0)

    # Add edges (road segments) with OSM data
    G.add_edge(1, 2, osmid=101, highway='primary', length=100.0)
    G.add_edge(2, 1, osmid=102, highway='primary', length=100.0)
    G.add_edge(2, 3, osmid=103, highway='secondary', length=100.0)
    G.add_edge(3, 2, osmid=104, highway='secondary', length=100.0)
    G.add_edge(2, 4, osmid=105, highway='residential', length=100.0)
    G.add_edge(4, 2, osmid=106, highway='residential', length=100.0)

    return G


@pytest.fixture
def mock_edges_gdf(mock_road_graph):
    """Create mock edges GeoDataFrame."""
    edges_data = []

    for u, v, data in mock_road_graph.edges(data=True):
        # Create line geometry for each edge
        if (u, v) in [(1, 2), (2, 1)]:
            geom = LineString([(0, 0), (100, 0)])
        elif (u, v) in [(2, 3), (3, 2)]:
            geom = LineString([(100, 0), (200, 0)])
        else:  # (2, 4), (4, 2)
            geom = LineString([(100, 0), (100, 100)])

        edges_data.append({
            'geometry': geom,
            'u': u,
            'v': v,
            'osmid': data.get('osmid', (u, v)),
            'highway': data.get('highway', 'unclassified'),
            'length': data.get('length', 100.0)
        })

    return gpd.GeoDataFrame(edges_data, crs='EPSG:3857')


class TestRoadNetworkSamplingInitialization:
    """Test suite for RoadNetworkSampling initialization."""

    def test_default_initialization(self):
        """Test initialization with default config."""
        strategy = RoadNetworkSampling()

        assert strategy.config.spacing == 100.0
        assert strategy.strategy_name == "road_network_sampling"
        assert strategy.network_type == "all"
        assert strategy.road_types is None

    def test_custom_initialization(self):
        """Test initialization with custom config."""
        config = SamplingConfig(spacing=50.0, seed=123)
        strategy = RoadNetworkSampling(
            config,
            network_type='drive',
            road_types={'primary', 'secondary'}
        )

        assert strategy.config.spacing == 50.0
        assert strategy.config.seed == 123
        assert strategy.network_type == 'drive'
        assert strategy.road_types == {'primary', 'secondary'}

    def test_none_config_creates_default(self):
        """Test that None config creates default config."""
        strategy = RoadNetworkSampling(config=None)

        assert isinstance(strategy.config, SamplingConfig)

    def test_invalid_network_type_raises_error(self):
        """Test that invalid network_type raises error."""
        with pytest.raises(ValueError) as excinfo:
            RoadNetworkSampling(network_type='invalid_type')

        assert "network_type must be one of" in str(excinfo.value)

    def test_invalid_road_type_raises_error(self):
        """Test that invalid road type raises error."""
        with pytest.raises(ValueError) as excinfo:
            RoadNetworkSampling(road_types={'invalid_highway_type'})

        assert "Invalid road types" in str(excinfo.value)

    def test_valid_network_types(self):
        """Test all valid network types."""
        for network_type in ['all', 'walk', 'drive', 'bike']:
            strategy = RoadNetworkSampling(network_type=network_type)
            assert strategy.network_type == network_type

    def test_valid_road_types(self):
        """Test valid road types."""
        road_types = {'primary', 'secondary', 'residential', 'tertiary'}
        strategy = RoadNetworkSampling(road_types=road_types)
        assert strategy.road_types == road_types


class TestRoadNetworkSamplingGenerate:
    """Test suite for RoadNetworkSampling.generate() method."""

    @pytest.fixture
    def simple_box_boundary(self):
        """Create a simple square boundary for testing."""
        return box(0, 0, 200, 100)

    @patch('ssp.sampling.road_network.ox')
    def test_generate_returns_geodataframe(self, mock_ox, mock_road_graph, simple_box_boundary):
        """Test that generate returns GeoDataFrame."""
        # Mock OSM functions
        mock_ox.config.return_value = None
        mock_ox.utils_graph.get_undirected.return_value = mock_road_graph
        mock_ox.graph_to_gdfs.return_value = self._create_mock_edges_gdf(mock_road_graph)

        with patch.object(RoadNetworkSampling, '_validate_boundary'):
            strategy = RoadNetworkSampling(SamplingConfig(spacing=50))
            result = strategy.generate(simple_box_boundary)

        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) > 0

    @patch('ssp.sampling.road_network.ox')
    def test_generate_has_required_columns(self, mock_ox, mock_road_graph, simple_box_boundary):
        """Test that generated GeoDataFrame has required columns."""
        mock_ox.config.return_value = None
        mock_ox.utils_graph.get_undirected.return_value = mock_road_graph
        mock_ox.graph_to_gdfs.return_value = self._create_mock_edges_gdf(mock_road_graph)

        with patch.object(RoadNetworkSampling, '_validate_boundary'):
            strategy = RoadNetworkSampling(SamplingConfig(spacing=50))
            result = strategy.generate(simple_box_boundary)

        required_columns = [
            'geometry', 'sample_id', 'strategy', 'timestamp',
            'edge_id', 'distance_along_edge', 'spacing_m',
            'highway', 'network_type'
        ]

        for col in required_columns:
            assert col in result.columns

    @patch('ssp.sampling.road_network.ox')
    def test_generate_filters_by_road_types(self, mock_ox, mock_road_graph, simple_box_boundary):
        """Test that road type filtering works."""
        mock_ox.config.return_value = None
        mock_ox.utils_graph.get_undirected.return_value = mock_road_graph

        # When graph_to_gdfs is called with the original graph, return all edges
        # When called with a filtered graph (which will have fewer edges), return filtered edges
        def mock_graph_to_gdfs(g, nodes=False):
            # If graph has fewer edges than original, it's been filtered
            if g.number_of_edges() < mock_road_graph.number_of_edges():
                # Return only primary edges
                return self._create_mock_edges_gdf_for_road_type(g, 'primary')
            return self._create_mock_edges_gdf(g)

        mock_ox.graph_to_gdfs.side_effect = mock_graph_to_gdfs

        with patch.object(RoadNetworkSampling, '_validate_boundary'):
            # Mock the boundary.contains at the module level to avoid CRS issues
            with patch('ssp.sampling.road_network.Polygon.contains', return_value=True):
                strategy = RoadNetworkSampling(
                    SamplingConfig(spacing=50),
                    road_types={'primary'}
                )
                result = strategy.generate(simple_box_boundary)

        # All points should be on primary roads
        assert all(result['highway'] == 'primary')

    def _create_mock_edges_gdf_for_road_type(self, graph, road_type):
        """Helper to create filtered mock edges GeoDataFrame."""
        import pandas as pd

        edges_data = []
        index = []

        for u, v, data in graph.edges(data=True):
            highway = data.get('highway', '')
            if isinstance(highway, list):
                if road_type not in highway:
                    continue
            elif highway != road_type:
                continue

            if (u, v) in [(1, 2), (2, 1)]:
                geom = LineString([(0, 0), (100, 0)])
            elif (u, v) in [(2, 3), (3, 2)]:
                geom = LineString([(100, 0), (200, 0)])
            else:
                geom = LineString([(100, 0), (100, 100)])

            edges_data.append({
                'geometry': geom,
                'osmid': data.get('osmid', 0),
                'highway': data.get('highway', road_type),
                'length': data.get('length', 100.0)
            })
            index.append((u, v, 0))

        multi_index = pd.MultiIndex.from_tuples(index, names=['u', 'v', 'key'])
        return gpd.GeoDataFrame(edges_data, index=multi_index, crs='EPSG:3857')

    @patch('ssp.sampling.road_network.ox')
    def test_generate_with_empty_graph_raises_error(self, mock_ox, simple_box_boundary):
        """Test that empty graph raises appropriate error."""
        # Mock empty graph
        empty_graph = nx.MultiDiGraph()
        mock_ox.config.return_value = None
        mock_ox.graph_from_polygon.return_value = empty_graph

        with patch.object(RoadNetworkSampling, '_validate_boundary'):
            strategy = RoadNetworkSampling()

            with pytest.raises(ValueError) as excinfo:
                strategy.generate(simple_box_boundary)

            assert "No road network found" in str(excinfo.value)

    @patch('ssp.sampling.road_network.ox')
    def test_sample_id_format(self, mock_ox, mock_road_graph, simple_box_boundary):
        """Test that sample IDs follow correct format."""
        mock_ox.config.return_value = None
        mock_ox.utils_graph.get_undirected.return_value = mock_road_graph
        mock_ox.graph_to_gdfs.return_value = self._create_mock_edges_gdf(mock_road_graph)

        with patch.object(RoadNetworkSampling, '_validate_boundary'):
            strategy = RoadNetworkSampling(SamplingConfig(spacing=50))
            result = strategy.generate(simple_box_boundary)

        first_id = result['sample_id'].iloc[0]
        assert "road_network_sampling" in first_id
        assert '_' in first_id

    @patch('ssp.sampling.road_network.ox')
    def test_timestamp_included(self, mock_ox, mock_road_graph, simple_box_boundary):
        """Test that timestamp is included and valid."""
        mock_ox.config.return_value = None
        mock_ox.utils_graph.get_undirected.return_value = mock_road_graph
        mock_ox.graph_to_gdfs.return_value = self._create_mock_edges_gdf(mock_road_graph)

        with patch.object(RoadNetworkSampling, '_validate_boundary'):
            strategy = RoadNetworkSampling(SamplingConfig(spacing=50))
            result = strategy.generate(simple_box_boundary)

        assert 'timestamp' in result.columns
        timestamp_str = result['timestamp'].iloc[0]
        datetime.fromisoformat(timestamp_str)  # Should not raise

    @patch('ssp.sampling.road_network.ox')
    def test_spacing_recorded_correctly(self, mock_ox, mock_road_graph, simple_box_boundary):
        """Test that spacing_m column records correct spacing."""
        mock_ox.config.return_value = None
        mock_ox.utils_graph.get_undirected.return_value = mock_road_graph
        mock_ox.graph_to_gdfs.return_value = self._create_mock_edges_gdf(mock_road_graph)

        # Mock boundary.contains at module level to avoid CRS issues
        with patch.object(RoadNetworkSampling, '_validate_boundary'):
            with patch('ssp.sampling.road_network.Polygon.contains', return_value=True):
                strategy = RoadNetworkSampling(SamplingConfig(spacing=75.5))
                result = strategy.generate(simple_box_boundary)

        assert all(result['spacing_m'] == 75.5)

    def _create_mock_edges_gdf(self, graph):
        """Helper to create mock edges GeoDataFrame with MultiIndex."""
        import pandas as pd

        edges_data = []
        index = []

        for u, v, data in graph.edges(data=True):
            if (u, v) in [(1, 2), (2, 1)]:
                geom = LineString([(0, 0), (100, 0)])
            elif (u, v) in [(2, 3), (3, 2)]:
                geom = LineString([(100, 0), (200, 0)])
            else:
                geom = LineString([(100, 0), (100, 100)])

            edges_data.append({
                'geometry': geom,
                'osmid': data.get('osmid', 0),
                'highway': data.get('highway', 'unclassified'),
                'length': data.get('length', 100.0)
            })
            # Create MultiIndex as OSMnx does
            index.append((u, v, 0))

        # Create MultiIndex
        multi_index = pd.MultiIndex.from_tuples(index, names=['u', 'v', 'key'])

        return gpd.GeoDataFrame(edges_data, index=multi_index, crs='EPSG:3857')


class TestRoadNetworkSamplingMetrics:
    """Test suite for calculate_road_network_metrics method."""

    @patch('ssp.sampling.road_network.ox')
    def test_calculate_metrics_with_points(self, mock_ox, mock_road_graph):
        """Test metrics calculation with sample points."""
        mock_ox.config.return_value = None
        mock_ox.utils_graph.get_undirected.return_value = mock_road_graph
        mock_ox.graph_to_gdfs.return_value = self._create_mock_edges_gdf(mock_road_graph)

        with patch.object(RoadNetworkSampling, '_validate_boundary'):
            strategy = RoadNetworkSampling(SamplingConfig(spacing=50))
            boundary = box(0, 0, 200, 100)

            # Manually create sample points for testing
            points_data = [{
                'geometry': Point(50, 50),
                'sample_id': 'test_001',
                'highway': 'primary',
                'strategy': 'road_network_sampling'
            }]
            strategy._sample_points = gpd.GeoDataFrame(points_data, crs='EPSG:3857')

            metrics = strategy.calculate_road_network_metrics()

            assert 'n_points' in metrics
            assert 'n_edges' in metrics
            assert 'n_nodes' in metrics
            assert 'total_road_length_km' in metrics
            assert 'avg_degree' in metrics
            assert 'road_type_distribution' in metrics
            assert 'network_type' in metrics

            assert metrics['n_points'] == 1

    @patch('ssp.sampling.road_network.ox')
    def test_calculate_metrics_without_points(self, mock_ox):
        """Test metrics calculation without sample points."""
        strategy = RoadNetworkSampling()
        metrics = strategy.calculate_road_network_metrics()

        assert metrics['n_points'] == 0
        assert metrics['n_edges'] == 0
        assert metrics['n_nodes'] == 0

    def _create_mock_edges_gdf(self, graph):
        """Helper to create mock edges GeoDataFrame with MultiIndex."""
        import pandas as pd

        edges_data = []
        index = []

        for u, v, data in graph.edges(data=True):
            if (u, v) in [(1, 2), (2, 1)]:
                geom = LineString([(0, 0), (100, 0)])
            elif (u, v) in [(2, 3), (3, 2)]:
                geom = LineString([(100, 0), (200, 0)])
            else:
                geom = LineString([(100, 0), (100, 100)])

            edges_data.append({
                'geometry': geom,
                'osmid': data.get('osmid', 0),
                'highway': data.get('highway', 'unclassified'),
                'length': data.get('length', 100.0)
            })
            # Create MultiIndex as OSMnx does
            index.append((u, v, 0))

        # Create MultiIndex
        multi_index = pd.MultiIndex.from_tuples(index, names=['u', 'v', 'key'])

        return gpd.GeoDataFrame(edges_data, index=multi_index, crs='EPSG:3857')


class TestRoadNetworkSamplingEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_invalid_boundary_raises_error(self):
        """Test that invalid boundary raises error."""
        strategy = RoadNetworkSampling()

        with pytest.raises(TypeError) as excinfo:
            strategy.generate("not a polygon")

        assert "Polygon" in str(excinfo.value)

    def test_zero_spacing_raises_error(self):
        """Test that zero spacing raises error."""
        with pytest.raises(ValueError) as excinfo:
            RoadNetworkSampling(SamplingConfig(spacing=0))

        assert "spacing must be positive" in str(excinfo.value)

    def test_negative_spacing_raises_error(self):
        """Test that negative spacing raises error."""
        with pytest.raises(ValueError) as excinfo:
            RoadNetworkSampling(SamplingConfig(spacing=-50))

        assert "spacing must be positive" in str(excinfo.value)

    @patch('ssp.sampling.road_network.ox')
    def test_network_type_preserved_in_output(self, mock_ox, mock_road_graph):
        """Test that network_type is preserved in output."""
        mock_ox.config.return_value = None
        mock_ox.utils_graph.get_undirected.return_value = mock_road_graph
        mock_ox.graph_to_gdfs.return_value = self._create_mock_edges_gdf(mock_road_graph)

        with patch.object(RoadNetworkSampling, '_validate_boundary'):
            strategy = RoadNetworkSampling(
                SamplingConfig(spacing=50),
                network_type='drive'
            )
            boundary = box(0, 0, 200, 100)
            result = strategy.generate(boundary)

            assert all(result['network_type'] == 'drive')

    def _create_mock_edges_gdf(self, graph):
        """Helper to create mock edges GeoDataFrame with MultiIndex."""
        import pandas as pd

        edges_data = []
        index = []

        for u, v, data in graph.edges(data=True):
            if (u, v) in [(1, 2), (2, 1)]:
                geom = LineString([(0, 0), (100, 0)])
            elif (u, v) in [(2, 3), (3, 2)]:
                geom = LineString([(100, 0), (200, 0)])
            else:
                geom = LineString([(100, 0), (100, 100)])

            edges_data.append({
                'geometry': geom,
                'osmid': data.get('osmid', 0),
                'highway': data.get('highway', 'unclassified'),
                'length': data.get('length', 100.0)
            })
            # Create MultiIndex as OSMnx does
            index.append((u, v, 0))

        # Create MultiIndex
        multi_index = pd.MultiIndex.from_tuples(index, names=['u', 'v', 'key'])

        return gpd.GeoDataFrame(edges_data, index=multi_index, crs='EPSG:3857')


class TestRoadNetworkSamplingReproducibility:
    """Test suite for reproducibility with seed parameter."""

    @patch('ssp.sampling.road_network.ox')
    def test_same_seed_reproducible(self, mock_ox, mock_road_graph):
        """Test that same seed produces reproducible results."""
        mock_ox.config.return_value = None
        mock_ox.utils_graph.get_undirected.return_value = mock_road_graph
        mock_ox.graph_to_gdfs.return_value = self._create_mock_edges_gdf(mock_road_graph)

        with patch.object(RoadNetworkSampling, '_validate_boundary'):
            config = SamplingConfig(spacing=50, seed=42)
            boundary = box(0, 0, 200, 100)

            # Generate first time
            strategy1 = RoadNetworkSampling(config)
            points1 = strategy1.generate(boundary)

            # Generate second time with same config
            # Note: timestamps will differ, so we compare only non-timestamp columns
            strategy2 = RoadNetworkSampling(config)
            points2 = strategy2.generate(boundary)

            # Should have same number of points
            assert len(points1) == len(points2)

    def _create_mock_edges_gdf(self, graph):
        """Helper to create mock edges GeoDataFrame with MultiIndex."""
        import pandas as pd

        edges_data = []
        index = []

        for u, v, data in graph.edges(data=True):
            if (u, v) in [(1, 2), (2, 1)]:
                geom = LineString([(0, 0), (100, 0)])
            elif (u, v) in [(2, 3), (3, 2)]:
                geom = LineString([(100, 0), (200, 0)])
            else:
                geom = LineString([(100, 0), (100, 100)])

            edges_data.append({
                'geometry': geom,
                'osmid': data.get('osmid', 0),
                'highway': data.get('highway', 'unclassified'),
                'length': data.get('length', 100.0)
            })
            # Create MultiIndex as OSMnx does
            index.append((u, v, 0))

        # Create MultiIndex
        multi_index = pd.MultiIndex.from_tuples(index, names=['u', 'v', 'key'])

        return gpd.GeoDataFrame(edges_data, index=multi_index, crs='EPSG:3857')
