"""
Unit tests for metadata management module.

Tests metadata models, serialization, validation, and export functionality.
"""

import pytest
import json
import tempfile
import yaml
from pathlib import Path
from shapely.geometry import box
from datetime import datetime
import sys
import platform

import sys
sys.path.insert(0, '/Users/bruce/10_School/11_MSC-Politecnico di Milano/03-Third Sem-Archive/GProcessing/2025-2026/GProcessing2025/src')

from ssp import GridSampling, SamplingConfig, SamplingMetadata
from ssp.metadata import (
    SamplingStrategyType,
    BoundaryMetadata,
    SamplingParametersMetadata,
    ExecutionMetadata,
    DataSourceMetadata,
    ResultsMetadata,
    MetadataSerializer,
    MetadataValidator,
    MetadataExporter,
    MetadataBatchSerializer,
    MetadataValidationError,
    quick_validate
)


class TestMetadataModels:
    """Test metadata data models."""

    def test_boundary_metadata_creation(self):
        """Test BoundaryMetadata creation."""
        boundary = box(0, 0, 1000, 1000)

        meta = BoundaryMetadata(
            geometry_wkt=boundary.wkt,
            crs="EPSG:4326",
            area_km2=1.0,
            bounds=(0, 0, 1000, 1000),
            source="user_provided",
            description="Test boundary"
        )

        assert meta.crs == "EPSG:4326"
        assert meta.area_km2 == 1.0
        assert meta.source == "user_provided"
        assert meta.description == "Test boundary"

    def test_sampling_parameters_metadata(self):
        """Test SamplingParametersMetadata creation."""
        meta = SamplingParametersMetadata(
            spacing=100.0,
            seed=42,
            crs="EPSG:4326",
            strategy_type="grid_sampling",
            additional_params={"network_type": "drive"}
        )

        assert meta.spacing == 100.0
        assert meta.seed == 42
        assert meta.strategy_type == "grid_sampling"
        assert "network_type" in meta.additional_params

    def test_execution_metadata(self):
        """Test ExecutionMetadata creation."""
        meta = ExecutionMetadata(
            timestamp="2025-01-22T10:00:00",
            python_version="3.10.0",
            ssp_version="0.1.0",
            os_info="Darwin 25.1.0",
            hostname="test-machine",
            user="test-user",
            runtime_seconds=5.5
        )

        assert meta.python_version == "3.10.0"
        assert meta.ssp_version == "0.1.0"
        assert meta.runtime_seconds == 5.5

    def test_data_source_metadata(self):
        """Test DataSourceMetadata creation."""
        meta = DataSourceMetadata(
            source_type="osm",
            source_url="https://www.openstreetmap.org/",
            access_timestamp="2025-01-22T10:00:00",
            version="2025-01-22",
            quality_notes="Good data quality"
        )

        assert meta.source_type == "osm"
        assert meta.source_url == "https://www.openstreetmap.org/"
        assert meta.version == "2025-01-22"

    def test_results_metadata(self):
        """Test ResultsMetadata creation."""
        meta = ResultsMetadata(
            n_points=100,
            density_pts_per_km2=50.0,
            coverage_metrics={"area_km2": 2.0},
            strategy_metrics={"n_edges": 50}
        )

        assert meta.n_points == 100
        assert meta.density_pts_per_km2 == 50.0
        assert "area_km2" in meta.coverage_metrics

    def test_sampling_metadata_creation(self):
        """Test SamplingMetadata creation."""
        boundary = box(0, 0, 1000, 1000)

        meta = SamplingMetadata(
            protocol_id="test_001",
            protocol_name="Test Protocol",
            description="Test description",
            version="1.0.0",
            author="Test Author",
            institution="Test Institution",
            contact="test@example.com"
        )

        assert meta.protocol_id == "test_001"
        assert meta.protocol_name == "Test Protocol"
        assert meta.version == "1.0.0"

    def test_sampling_metadata_to_dict(self):
        """Test SamplingMetadata serialization to dictionary."""
        boundary = box(0, 0, 1000, 1000)

        boundary_meta = BoundaryMetadata(
            geometry_wkt=boundary.wkt,
            crs="EPSG:4326",
            area_km2=1.0,
            bounds=(0, 0, 1000, 1000)
        )

        params_meta = SamplingParametersMetadata(
            spacing=100.0,
            seed=42,
            crs="EPSG:4326",
            strategy_type="grid_sampling"
        )

        meta = SamplingMetadata(
            protocol_id="test_001",
            protocol_name="Test Protocol",
            description="Test description",
            boundary=boundary_meta,
            parameters=params_meta
        )

        data = meta.to_dict()

        assert data['protocol_id'] == "test_001"
        assert 'boundary' in data
        assert 'parameters' in data
        assert data['boundary']['crs'] == "EPSG:4326"

    def test_sampling_metadata_from_dict(self):
        """Test SamplingMetadata deserialization from dictionary."""
        data = {
            'protocol_id': 'test_001',
            'protocol_name': 'Test Protocol',
            'description': 'Test description',
            'version': '1.0.0',
            'created_at': '2025-01-22T10:00:00',
            'boundary': {
                'geometry_wkt': 'POLYGON ((0 0, 1000 0, 1000 1000, 0 1000, 0 0))',
                'crs': 'EPSG:4326',
                'area_km2': 1.0,
                'bounds': (0, 0, 1000, 1000),
                'source': 'user_provided'
            },
            'parameters': {
                'spacing': 100.0,
                'seed': 42,
                'crs': 'EPSG:4326',
                'strategy_type': 'grid_sampling',
                'additional_params': {}
            },
            'data_sources': [],
            'tags': [],
            'custom_fields': {}
        }

        meta = SamplingMetadata.from_dict(data)

        assert meta.protocol_id == 'test_001'
        assert meta.protocol_name == 'Test Protocol'
        assert meta.boundary is not None
        assert meta.parameters is not None

    def test_sampling_metadata_from_strategy(self):
        """Test creating SamplingMetadata from GridSampling strategy."""
        boundary = box(0, 0, 1000, 1000)
        config = SamplingConfig(spacing=100, seed=42)
        strategy = GridSampling(config)
        points = strategy.generate(boundary)

        metadata = SamplingMetadata.create_from_strategy(
            strategy=strategy,
            boundary=boundary,
            protocol_name="Test Grid Study",
            description="Test grid sampling protocol",
            author="Test Author"
        )

        assert metadata.protocol_name == "Test Grid Study"
        assert metadata.boundary is not None
        assert metadata.parameters is not None
        assert metadata.execution is not None
        assert metadata.results is not None
        assert metadata.author == "Test Author"

        # Check boundary metadata
        assert metadata.boundary.crs == "EPSG:4326"
        assert metadata.boundary.area_km2 > 0

        # Check parameters metadata
        assert metadata.parameters.spacing == 100
        assert metadata.parameters.seed == 42
        assert metadata.parameters.strategy_type == "grid_sampling"

        # Check execution metadata
        assert metadata.execution.ssp_version is not None
        assert metadata.execution.python_version is not None

        # Check results metadata
        assert metadata.results.n_points == len(points)
        assert metadata.results.density_pts_per_km2 > 0


class TestMetadataSerializer:
    """Test metadata serialization."""

    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        meta = SamplingMetadata(
            protocol_id="test_001",
            protocol_name="Test Protocol",
            description="Test description"
        )

        serializer = MetadataSerializer(format='json')

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            # Serialize
            serializer.to_json(meta, filepath)

            # Deserialize
            loaded = serializer.from_json(filepath)

            assert loaded.protocol_id == meta.protocol_id
            assert loaded.protocol_name == meta.protocol_name
            assert loaded.description == meta.description
        finally:
            Path(filepath).unlink()

    def test_yaml_serialization(self):
        """Test YAML serialization and deserialization."""
        meta = SamplingMetadata(
            protocol_id="test_001",
            protocol_name="Test Protocol",
            description="Test description"
        )

        serializer = MetadataSerializer(format='yaml')

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            filepath = f.name

        try:
            # Serialize
            serializer.to_yaml(meta, filepath)

            # Deserialize
            loaded = serializer.from_yaml(filepath)

            assert loaded.protocol_id == meta.protocol_id
            assert loaded.protocol_name == meta.protocol_name
        finally:
            Path(filepath).unlink()

    def test_json_string_serialization(self):
        """Test JSON serialization to string (no file)."""
        meta = SamplingMetadata(
            protocol_id="test_001",
            protocol_name="Test Protocol",
            description="Test description"
        )

        serializer = MetadataSerializer(format='json')

        # Serialize to string
        json_str = serializer.to_json(meta, filepath=None)

        assert isinstance(json_str, str)
        assert 'test_001' in json_str
        assert 'Test Protocol' in json_str

        # Deserialize from string
        loaded = serializer.from_json(json_str)
        assert loaded.protocol_id == "test_001"

    def test_yaml_string_serialization(self):
        """Test YAML serialization to string (no file)."""
        meta = SamplingMetadata(
            protocol_id="test_001",
            protocol_name="Test Protocol",
            description="Test description"
        )

        serializer = MetadataSerializer(format='yaml')

        # Serialize to string
        yaml_str = serializer.to_yaml(meta, filepath=None)

        assert isinstance(yaml_str, str)
        assert 'test_001' in yaml_str
        assert 'Test Protocol' in yaml_str

        # Deserialize from string
        loaded = serializer.from_yaml(yaml_str)
        assert loaded.protocol_id == "test_001"


class TestMetadataValidator:
    """Test metadata validation."""

    def test_valid_metadata(self):
        """Test validation of valid metadata."""
        boundary = box(0, 0, 1000, 1000)

        meta = SamplingMetadata(
            protocol_id="test_001",
            protocol_name="Test Protocol",
            description="Test description",
            version="1.0.0",
            created_at="2025-01-22T10:00:00"
        )

        validator = MetadataValidator()
        is_valid, errors = validator.validate(meta)

        assert is_valid
        assert len(errors) == 0

    def test_missing_required_fields(self):
        """Test validation fails with missing required fields."""
        meta = SamplingMetadata(
            protocol_id="",  # Invalid (empty)
            protocol_name="",  # Invalid (empty)
            description=""  # Invalid (empty)
        )

        validator = MetadataValidator()
        is_valid, errors = validator.validate(meta)

        assert not is_valid
        assert len(errors) > 0
        assert any("protocol_id" in err for err in errors)

    def test_invalid_protocol_id_format(self):
        """Test validation fails with invalid protocol_id format."""
        meta = SamplingMetadata(
            protocol_id="invalid id with spaces!",  # Invalid format
            protocol_name="Test Protocol",
            description="Test description"
        )

        validator = MetadataValidator()
        is_valid, errors = validator.validate(meta)

        assert not is_valid
        assert any("protocol_id" in err and "alphanumeric" in err for err in errors)

    def test_invalid_timestamp_format(self):
        """Test validation fails with invalid timestamp format."""
        meta = SamplingMetadata(
            protocol_id="test_001",
            protocol_name="Test Protocol",
            description="Test description",
            created_at="invalid-timestamp"  # Invalid format
        )

        validator = MetadataValidator()
        is_valid, errors = validator.validate(meta)

        assert not is_valid
        assert any("created_at" in err and "ISO 8601" in err for err in errors)

    def test_invalid_spacing(self):
        """Test validation fails with invalid spacing."""
        boundary = box(0, 0, 1000, 1000)

        boundary_meta = BoundaryMetadata(
            geometry_wkt=boundary.wkt,
            crs="EPSG:4326",
            area_km2=1.0,
            bounds=(0, 0, 1000, 1000)
        )

        params_meta = SamplingParametersMetadata(
            spacing=-100.0,  # Invalid (negative)
            seed=42,
            crs="EPSG:4326",
            strategy_type="grid_sampling"
        )

        meta = SamplingMetadata(
            protocol_id="test_001",
            protocol_name="Test Protocol",
            description="Test description",
            boundary=boundary_meta,
            parameters=params_meta
        )

        validator = MetadataValidator()
        is_valid, errors = validator.validate(meta)

        assert not is_valid
        assert any("spacing" in err and "positive" in err for err in errors)

    def test_quick_validate(self):
        """Test quick_validate convenience function."""
        meta = SamplingMetadata(
            protocol_id="test_001",
            protocol_name="Test Protocol",
            description="Test description",
            version="1.0.0",
            created_at="2025-01-22T10:00:00"
        )

        assert quick_validate(meta) is True


class TestMetadataExporter:
    """Test metadata export functionality."""

    def test_export_json(self):
        """Test JSON export."""
        meta = SamplingMetadata(
            protocol_id="test_001",
            protocol_name="Test Protocol",
            description="Test description"
        )

        exporter = MetadataExporter()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            exporter.export_json(meta, filepath)

            # Verify file exists and contains data
            assert Path(filepath).exists()

            with open(filepath, 'r') as f:
                data = json.load(f)

            assert data['protocol_id'] == 'test_001'
        finally:
            Path(filepath).unlink()

    def test_export_yaml(self):
        """Test YAML export."""
        meta = SamplingMetadata(
            protocol_id="test_001",
            protocol_name="Test Protocol",
            description="Test description"
        )

        exporter = MetadataExporter()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            filepath = f.name

        try:
            exporter.export_yaml(meta, filepath)

            # Verify file exists and contains data
            assert Path(filepath).exists()

            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)

            assert data['protocol_id'] == 'test_001'
        finally:
            Path(filepath).unlink()

    def test_export_csv(self):
        """Test CSV export."""
        boundary = box(0, 0, 1000, 1000)

        boundary_meta = BoundaryMetadata(
            geometry_wkt=boundary.wkt,
            crs="EPSG:4326",
            area_km2=1.0,
            bounds=(0, 0, 1000, 1000)
        )

        meta = SamplingMetadata(
            protocol_id="test_001",
            protocol_name="Test Protocol",
            description="Test description",
            boundary=boundary_meta
        )

        exporter = MetadataExporter()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            filepath = f.name

        try:
            exporter.export_csv(meta, filepath)

            # Verify file exists
            assert Path(filepath).exists()

            # Read and verify content
            with open(filepath, 'r') as f:
                content = f.read()

            assert 'protocol_id' in content
            assert 'test_001' in content
        finally:
            Path(filepath).unlink()

    def test_export_html_report(self):
        """Test HTML report export."""
        meta = SamplingMetadata(
            protocol_id="test_001",
            protocol_name="Test Protocol",
            description="Test description",
            author="Test Author"
        )

        exporter = MetadataExporter()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            filepath = f.name

        try:
            exporter.export_html_report(meta, filepath)

            # Verify file exists
            assert Path(filepath).exists()

            # Read and verify content
            html_content = Path(filepath).read_text()

            assert 'test_001' in html_content
            assert 'Test Protocol' in html_content
            assert 'Test Author' in html_content
            assert '<html>' in html_content
        finally:
            Path(filepath).unlink()

    def test_export_all(self):
        """Test export to all formats."""
        boundary = box(0, 0, 1000, 1000)
        config = SamplingConfig(spacing=100, seed=42)
        strategy = GridSampling(config)
        points = strategy.generate(boundary)

        metadata = SamplingMetadata.create_from_strategy(
            strategy=strategy,
            boundary=boundary,
            protocol_name="Test Study",
            description="Test description"
        )

        exporter = MetadataExporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            exported = exporter.export_all(
                metadata,
                points,
                output_dir=tmpdir,
                base_name="test_export"
            )

            # Check all formats were exported
            assert 'geojson' in exported
            assert 'yaml' in exported
            assert 'json' in exported
            assert 'csv' in exported
            assert 'html' in exported

            # Verify files exist
            for format_name, filepath in exported.items():
                assert Path(filepath).exists()


class TestMetadataBatchSerializer:
    """Test batch serialization."""

    def test_batch_serialization(self):
        """Test serializing multiple metadata files."""
        meta1 = SamplingMetadata(
            protocol_id="test_001",
            protocol_name="Protocol 1",
            description="Test 1"
        )

        meta2 = SamplingMetadata(
            protocol_id="test_002",
            protocol_name="Protocol 2",
            description="Test 2"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            batch = MetadataBatchSerializer()
            batch.add(meta1, f"{tmpdir}/meta1.json", format='json')
            batch.add(meta2, f"{tmpdir}/meta2.json", format='json')

            assert len(batch) == 2

            # Write all
            batch.write_all()

            # Verify files exist
            assert Path(f"{tmpdir}/meta1.json").exists()
            assert Path(f"{tmpdir}/meta2.json").exists()

    def test_batch_clear(self):
        """Test clearing batch queue."""
        meta = SamplingMetadata(
            protocol_id="test_001",
            protocol_name="Test Protocol",
            description="Test description"
        )

        batch = MetadataBatchSerializer()
        batch.add(meta, "test.json", format='json')

        assert len(batch) == 1

        batch.clear()

        assert len(batch) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
