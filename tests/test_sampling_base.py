"""
Unit tests for sampling base module.

Tests SamplingConfig and SamplingStrategy base class functionality.
"""

from datetime import datetime
import pytest
from shapely.geometry import Polygon, box, Point
from shapely import wkt
import geopandas as gpd

from svipro.sampling.base import SamplingConfig, SamplingStrategy


class TestSamplingConfig:
    """Test suite for SamplingConfig dataclass."""

    def test_default_initialization(self):
        """Test default configuration values."""
        config = SamplingConfig()

        assert config.spacing == 100.0
        assert config.crs == "EPSG:4326"
        assert config.seed == 42
        assert config.boundary is None
        assert config.metadata == {}

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        boundary = box(0, 0, 1000, 1000)
        config = SamplingConfig(
            spacing=50.0,
            crs="EPSG:3857",
            seed=123,
            boundary=boundary,
            metadata={'key': 'value'}
        )

        assert config.spacing == 50.0
        assert config.crs == "EPSG:3857"
        assert config.seed == 123
        assert config.boundary == boundary
        assert config.metadata == {'key': 'value'}

    def test_validation_positive_spacing(self):
        """Test that positive spacing is required."""
        with pytest.raises(ValueError) as excinfo:
            SamplingConfig(spacing=-10.0)

        assert "spacing must be positive" in str(excinfo.value)

    def test_validation_zero_spacing(self):
        """Test that zero spacing is rejected."""
        with pytest.raises(ValueError) as excinfo:
            SamplingConfig(spacing=0.0)

        assert "spacing must be positive" in str(excinfo.value)

    def test_validation_crs_not_empty(self):
        """Test that CRS must be a non-empty string."""
        with pytest.raises(ValueError) as excinfo:
            SamplingConfig(crs="")

        assert "crs must be a non-empty string" in str(excinfo.value)

    def test_validation_crs_is_string(self):
        """Test that CRS must be a string."""
        with pytest.raises(ValueError) as excinfo:
            SamplingConfig(crs=None)

        assert "crs must be a non-empty string" in str(excinfo.value)

    def test_validation_non_negative_seed(self):
        """Test that seed must be non-negative."""
        with pytest.raises(ValueError) as excinfo:
            SamplingConfig(seed=-1)

        assert "seed must be non-negative" in str(excinfo.value)

    def test_to_dict(self):
        """Test serialization to dictionary."""
        boundary = box(0, 0, 1000, 1000)
        config = SamplingConfig(spacing=50.0, crs="EPSG:3857", boundary=boundary)

        config_dict = config.to_dict()

        assert config_dict['spacing'] == 50.0
        assert config_dict['crs'] == "EPSG:3857"
        assert config_dict['seed'] == 42
        assert config_dict['boundary'] == boundary.wkt
        assert config_dict['metadata'] == {}

    def test_to_dict_without_boundary(self):
        """Test serialization when boundary is None."""
        config = SamplingConfig()

        config_dict = config.to_dict()

        assert config_dict['boundary'] is None

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        boundary = box(0, 0, 1000, 1000)
        data = {
            'spacing': 75.0,
            'crs': 'EPSG:32633',
            'seed': 999,
            'boundary': boundary.wkt,
            'metadata': {'custom': 'data'}
        }

        config = SamplingConfig.from_dict(data)

        assert config.spacing == 75.0
        assert config.crs == 'EPSG:32633'
        assert config.seed == 999
        assert config.boundary == boundary
        assert config.metadata == {'custom': 'data'}

    def test_from_dict_missing_required_keys(self):
        """Test that missing required keys raise ValueError."""
        data = {'spacing': 100.0}  # Missing 'crs' and 'seed'

        with pytest.raises(ValueError) as excinfo:
            SamplingConfig.from_dict(data)

        assert "Missing required keys" in str(excinfo.value)

    def test_from_dict_without_boundary(self):
        """Test deserialization when boundary is None."""
        data = {
            'spacing': 100.0,
            'crs': 'EPSG:4326',
            'seed': 42,
            'boundary': None
        }

        config = SamplingConfig.from_dict(data)

        assert config.boundary is None

    def test_serialization_roundtrip(self):
        """Test that to_dict and from_dict are inverses."""
        original = SamplingConfig(
            spacing=150.0,
            crs="EPSG:32633",
            seed=456,
            metadata={'test': 'value'}
        )

        # Serialize and deserialize
        config_dict = original.to_dict()
        restored = SamplingConfig.from_dict(config_dict)

        # Check all attributes match
        assert restored.spacing == original.spacing
        assert restored.crs == original.crs
        assert restored.seed == original.seed
        assert restored.metadata == original.metadata


class ConcreteSamplingStrategy(SamplingStrategy):
    """Concrete implementation of SamplingStrategy for testing."""

    def generate(self, boundary: Polygon) -> gpd.GeoDataFrame:
        """Generate a simple test pattern - center point only."""
        self._validate_boundary(boundary)
        self.config.boundary = boundary
        self._generation_timestamp = datetime.now()

        center_point = boundary.centroid

        gdf = gpd.GeoDataFrame([{
            'geometry': center_point,
            'sample_id': 'test_0001',
            'strategy': 'concrete',
            'timestamp': self._generation_timestamp.isoformat()
        }], crs=self.config.crs)

        self._sample_points = gdf
        return gdf


class TestSamplingStrategy:
    """Test suite for SamplingStrategy base class."""

    def test_initialization_with_valid_config(self):
        """Test initialization with valid configuration."""
        config = SamplingConfig(spacing=100.0)
        strategy = ConcreteSamplingStrategy(config)

        assert strategy.config == config
        assert strategy._sample_points is None
        assert strategy.strategy_name == "ConcreteSamplingStrategy"

    def test_initialization_with_invalid_config_type(self):
        """Test that initialization with wrong config type raises TypeError."""
        with pytest.raises(TypeError) as excinfo:
            ConcreteSamplingStrategy(config="invalid")

        assert "must be SamplingConfig instance" in str(excinfo.value)

    def test_abstract_cannot_be_instantiated(self):
        """Test that SamplingStrategy cannot be instantiated directly."""
        config = SamplingConfig()

        with pytest.raises(TypeError):
            SamplingStrategy(config)

    def test_validate_boundary_with_valid_polygon(self):
        """Test boundary validation with valid polygon."""
        strategy = ConcreteSamplingStrategy(SamplingConfig())
        boundary = box(0, 0, 1000, 1000)

        # Should not raise any exception
        strategy._validate_boundary(boundary)

    def test_validate_boundary_with_wrong_type(self):
        """Test boundary validation rejects non-Polygon types."""
        strategy = ConcreteSamplingStrategy(SamplingConfig())

        with pytest.raises(TypeError) as excinfo:
            strategy._validate_boundary("not a polygon")

        assert "must be shapely Polygon" in str(excinfo.value)

    def test_validate_boundary_with_invalid_polygon(self):
        """Test boundary validation rejects invalid polygons."""
        strategy = ConcreteSamplingStrategy(SamplingConfig())

        # Create self-intersecting polygon (invalid)
        from shapely.geometry import Polygon
        invalid_boundary = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])

        with pytest.raises(ValueError) as excinfo:
            strategy._validate_boundary(invalid_boundary)

        assert "not a valid polygon" in str(excinfo.value)

    def test_validate_boundary_with_empty_polygon(self):
        """Test boundary validation rejects empty polygons."""
        strategy = ConcreteSamplingStrategy(SamplingConfig())

        empty_boundary = Polygon()

        with pytest.raises(ValueError) as excinfo:
            strategy._validate_boundary(empty_boundary)

        assert "cannot be empty" in str(excinfo.value)

    def test_get_sample_points_before_generation(self):
        """Test that getting points before generation raises ValueError."""
        strategy = ConcreteSamplingStrategy(SamplingConfig())

        with pytest.raises(ValueError) as excinfo:
            strategy.get_sample_points()

        assert "Call generate() method first" in str(excinfo.value)

    def test_get_sample_points_after_generation(self):
        """Test getting sample points after generation."""
        boundary = box(0, 0, 1000, 1000)
        strategy = ConcreteSamplingStrategy(SamplingConfig())

        points = strategy.generate(boundary)
        retrieved_points = strategy.get_sample_points()

        assert len(retrieved_points) == 1
        assert retrieved_points.equals(points)

    def test_get_config(self):
        """Test getting configuration."""
        config = SamplingConfig(spacing=50.0)
        strategy = ConcreteSamplingStrategy(config)

        retrieved_config = strategy.get_config()

        assert retrieved_config == config
        assert retrieved_config.spacing == 50.0

    def test_calculate_coverage_metrics_before_generation(self):
        """Test that metrics calculation before generation raises ValueError."""
        strategy = ConcreteSamplingStrategy(SamplingConfig())

        with pytest.raises(ValueError) as excinfo:
            strategy.calculate_coverage_metrics()

        assert "Call generate() method first" in str(excinfo.value)

    def test_calculate_coverage_metrics_after_generation(self):
        """Test calculating coverage metrics after generation."""
        boundary = box(0, 0, 1000, 1000)
        config = SamplingConfig(crs="EPSG:3857")  # Web Mercator projection
        strategy = ConcreteSamplingStrategy(config)
        strategy.generate(boundary)

        metrics = strategy.calculate_coverage_metrics()

        assert 'n_points' in metrics
        assert 'area_km2' in metrics
        assert 'density_pts_per_km2' in metrics
        assert 'bounds' in metrics
        assert 'crs' in metrics

        assert metrics['n_points'] == 1
        # Note: area calculation depends on CRS and may vary
        assert isinstance(metrics['area_km2'], (int, float))
        assert isinstance(metrics['density_pts_per_km2'], (int, float))

    def test_to_geojson_before_generation(self):
        """Test that export before generation raises ValueError."""
        strategy = ConcreteSamplingStrategy(SamplingConfig())

        with pytest.raises(ValueError) as excinfo:
            strategy.to_geojson("test.geojson")

        assert "Call generate() method first" in str(excinfo.value)

    def test_repr(self):
        """Test string representation."""
        config = SamplingConfig(spacing=75.0, crs="EPSG:3857", seed=123)
        strategy = ConcreteSamplingStrategy(config)

        repr_str = repr(strategy)

        assert "ConcreteSamplingStrategy" in repr_str
        assert "spacing=75.0m" in repr_str
        assert "crs='EPSG:3857'" in repr_str
        assert "seed=123" in repr_str
