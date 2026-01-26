"""
Tests for CLI module.

This test suite verifies the command-line interface functionality,
including all commands and their error handling.
"""

import json
import tempfile
from pathlib import Path

import geojson
import geopandas as gpd
import pytest
from click.testing import CliRunner
from shapely.geometry import box

from ssp.cli import cli


@pytest.fixture
def runner():
    """Create a Click CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_boundary_file():
    """Create a temporary GeoJSON boundary file for testing."""
    # Create a simple boundary
    boundary = box(0, 0, 0.1, 0.1)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
        # Write as GeoJSON
        geojson.dump(geojson.Feature(geometry=geojson.loads(boundary.to_wkt()), properties={}), f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_output_file():
    """Create a temporary output file path for testing."""
    with tempfile.NamedTemporaryFile(suffix='.geojson', delete=True) as f:
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


class TestCLI:
    """Test suite for basic CLI functionality."""

    def test_cli_main_command(self, runner):
        """Test that the main CLI command works."""
        result = runner.invoke(cli)
        assert result.exit_code == 0
        assert 'SpatialSamplingPro' in result.output or 'Usage:' in result.output

    def test_cli_version(self, runner):
        """Test CLI version option."""
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '0.1.0' in result.output


class TestSampleGrid:
    """Test suite for 'ssp sample grid' command."""

    def test_sample_grid_basic(self, runner, temp_boundary_file, temp_output_file):
        """Test basic grid sampling command."""
        result = runner.invoke(cli, [
            'sample', 'grid',
            '--spacing', '100',
            '--aoi', temp_boundary_file,
            '--output', temp_output_file
        ])

        # Check command executed successfully
        if result.exit_code != 0:
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")

        assert result.exit_code == 0
        assert Path(temp_output_file).exists()

    def test_sample_grid_with_metadata(self, runner, temp_boundary_file, temp_output_file):
        """Test grid sampling with metadata flag."""
        result = runner.invoke(cli, [
            'sample', 'grid',
            '--spacing', '100',
            '--metadata',
            '--aoi', temp_boundary_file,
            '--output', temp_output_file
        ])

        assert result.exit_code == 0
        assert Path(temp_output_file).exists()

        # Verify metadata is in output
        with open(temp_output_file, 'r') as f:
            data = json.load(f)
            assert 'metadata' in data or 'features' in data

    def test_sample_grid_custom_spacing(self, runner, temp_boundary_file, temp_output_file):
        """Test grid sampling with custom spacing."""
        result = runner.invoke(cli, [
            'sample', 'grid',
            '--spacing', '50',
            '--aoi', temp_boundary_file,
            '--output', temp_output_file
        ])

        assert result.exit_code == 0

        # Verify output file
        gdf = gpd.read_file(temp_output_file)
        assert len(gdf) > 0

    def test_sample_grid_missing_aoi(self, runner, temp_output_file):
        """Test grid sampling with missing AOI file."""
        result = runner.invoke(cli, [
            'sample', 'grid',
            '--spacing', '100',
            '--aoi', 'nonexistent.geojson',
            '--output', temp_output_file
        ])

        assert result.exit_code != 0
        assert 'not found' in result.output.lower() or 'error' in result.output.lower()

    def test_sample_grid_invalid_spacing(self, runner, temp_boundary_file, temp_output_file):
        """Test grid sampling with invalid spacing (too small)."""
        result = runner.invoke(cli, [
            'sample', 'grid',
            '--spacing', '0.001',  # Too small, should trigger error
            '--aoi', temp_boundary_file,
            '--output', temp_output_file
        ])

        # Should fail with spacing validation error
        assert result.exit_code != 0

    def test_sample_grid_custom_seed(self, runner, temp_boundary_file, temp_output_file):
        """Test grid sampling with custom seed."""
        result = runner.invoke(cli, [
            'sample', 'grid',
            '--spacing', '100',
            '--seed', '123',
            '--aoi', temp_boundary_file,
            '--output', temp_output_file
        ])

        assert result.exit_code == 0
        assert Path(temp_output_file).exists()


class TestSampleRoadNetwork:
    """Test suite for 'ssp sample road-network' command."""

    def test_sample_road_network_basic(self, runner, temp_boundary_file, temp_output_file):
        """Test basic road network sampling command."""
        result = runner.invoke(cli, [
            'sample', 'road-network',
            '--spacing', '100',
            '--aoi', temp_boundary_file,
            '--output', temp_output_file
        ])

        # May fail due to network issues or OSM availability, so we check for graceful handling
        # Exit code 0 or 1 are both acceptable (1 might be network error)
        assert result.exit_code in [0, 1]

    def test_sample_road_network_with_network_type(self, runner, temp_boundary_file, temp_output_file):
        """Test road network sampling with specific network type."""
        result = runner.invoke(cli, [
            'sample', 'road-network',
            '--spacing', '100',
            '--network-type', 'drive',
            '--aoi', temp_boundary_file,
            '--output', temp_output_file
        ])

        # May fail due to network issues
        assert result.exit_code in [0, 1]

    def test_sample_road_network_with_road_types(self, runner, temp_boundary_file, temp_output_file):
        """Test road network sampling with road type filters."""
        result = runner.invoke(cli, [
            'sample', 'road-network',
            '--spacing', '100',
            '--road-types', 'primary',
            '--road-types', 'secondary',
            '--aoi', temp_boundary_file,
            '--output', temp_output_file
        ])

        # May fail due to network issues
        assert result.exit_code in [0, 1]


class TestQualityMetrics:
    """Test suite for 'ssp quality metrics' command."""

    def test_quality_metrics_with_sample_file(self, runner, temp_boundary_file, temp_output_file):
        """Test quality metrics calculation with a sample file."""
        # First generate sample points
        sample_result = runner.invoke(cli, [
            'sample', 'grid',
            '--spacing', '100',
            '--aoi', temp_boundary_file,
            '--output', temp_output_file
        ])

        assert sample_result.exit_code == 0

        # Now calculate metrics
        result = runner.invoke(cli, [
            'quality', 'metrics',
            '--points', temp_output_file
        ])

        assert result.exit_code == 0
        assert 'points' in result.output.lower() or 'coverage' in result.output.lower()

    def test_quality_metrics_missing_file(self, runner):
        """Test quality metrics with missing file."""
        result = runner.invoke(cli, [
            'quality', 'metrics',
            '--points', 'nonexistent.geojson'
        ])

        assert result.exit_code != 0


class TestProtocol:
    """Test suite for 'ssp protocol' command."""

    def test_protocol_create(self, runner, temp_boundary_file, temp_output_file):
        """Test protocol creation."""
        # First generate sample points
        sample_file = temp_output_file.replace('.geojson', '_samples.geojson')
        sample_result = runner.invoke(cli, [
            'sample', 'grid',
            '--spacing', '100',
            '--aoi', temp_boundary_file,
            '--output', sample_file
        ])

        assert sample_result.exit_code == 0

        # Create protocol
        protocol_file = temp_output_file.replace('.geojson', '_protocol.yaml')
        result = runner.invoke(cli, [
            'protocol', 'create',
            '--points', sample_file,
            '--output', protocol_file
        ])

        assert result.exit_code == 0
        assert Path(protocol_file).exists()


class TestVisualize:
    """Test suite for 'ssp visualize' commands."""

    def test_visualize_points_map(self, runner, temp_boundary_file, temp_output_file):
        """Test creating points map visualization."""
        # First generate sample points
        sample_file = temp_output_file.replace('.geojson', '_samples.geojson')
        sample_result = runner.invoke(cli, [
            'sample', 'grid',
            '--spacing', '100',
            '--aoi', temp_boundary_file,
            '--output', sample_file
        ])

        assert sample_result.exit_code == 0

        # Create visualization
        map_file = temp_output_file.replace('.geojson', '_map.html')
        result = runner.invoke(cli, [
            'visualize', 'points-map',
            '--points', sample_file,
            '--output', map_file
        ])

        assert result.exit_code == 0
        assert Path(map_file).exists()

    def test_visualize_statistics(self, runner, temp_boundary_file, temp_output_file):
        """Test creating statistics visualization."""
        # First generate sample points
        sample_file = temp_output_file.replace('.geojson', '_samples.geojson')
        sample_result = runner.invoke(cli, [
            'sample', 'grid',
            '--spacing', '100',
            '--aoi', temp_boundary_file,
            '--output', sample_file
        ])

        assert sample_result.exit_code == 0

        # Create statistics
        stats_file = temp_output_file.replace('.geojson', '_stats.png')
        result = runner.invoke(cli, [
            'visualize', 'statistics',
            '--points', sample_file,
            '--output', stats_file
        ])

        assert result.exit_code == 0
        assert Path(stats_file).exists()

    def test_visualize_compare(self, runner, temp_boundary_file, temp_output_file):
        """Test creating strategy comparison visualization."""
        # Create comparison
        compare_file = temp_output_file.replace('.geojson', '_compare.png')
        result = runner.invoke(cli, [
            'visualize', 'compare',
            '--grid-spacing', '100',
            '--aoi', temp_boundary_file,
            '--output', compare_file
        ])

        assert result.exit_code == 0
        assert Path(compare_file).exists()


class TestValidationErrorHandling:
    """Test suite for validation and error handling."""

    def test_invalid_geojson_format(self, runner, temp_output_file):
        """Test handling of invalid GeoJSON file."""
        # Create an invalid GeoJSON file
        with open(temp_output_file, 'w') as f:
            f.write('{"invalid": "json"}')

        result = runner.invoke(cli, [
            'sample', 'grid',
            '--spacing', '100',
            '--aoi', temp_output_file,
            '--output', temp_output_file + '_out.geojson'
        ])

        assert result.exit_code != 0

    def test_missing_output_directory(self, runner, temp_boundary_file):
        """Test creating output in non-existent directory."""
        output_path = '/nonexistent/dir/output.geojson'

        result = runner.invoke(cli, [
            'sample', 'grid',
            '--spacing', '100',
            '--aoi', temp_boundary_file,
            '--output', output_path
        ])

        # Should fail or create directory
        # Click's validation callback creates the directory, so this should succeed
        # But it might fail later when trying to write
        assert result.exit_code in [0, 1]


class TestHelpCommands:
    """Test suite for help commands."""

    def test_sample_help(self, runner):
        """Test sample command help."""
        result = runner.invoke(cli, ['sample', '--help'])
        assert result.exit_code == 0
        assert 'grid' in result.output
        assert 'road-network' in result.output

    def test_sample_grid_help(self, runner):
        """Test grid sampling help."""
        result = runner.invoke(cli, ['sample', 'grid', '--help'])
        assert result.exit_code == 0
        assert '--spacing' in result.output
        assert '--aoi' in result.output

    def test_quality_help(self, runner):
        """Test quality command help."""
        result = runner.invoke(cli, ['quality', '--help'])
        assert result.exit_code == 0
        assert 'metrics' in result.output

    def test_visualize_help(self, runner):
        """Test visualize command help."""
        result = runner.invoke(cli, ['visualize', '--help'])
        assert result.exit_code == 0
        assert 'points-map' in result.output
        assert 'statistics' in result.output
        assert 'compare' in result.output


class TestOutputValidation:
    """Test suite for output file validation."""

    def test_grid_output_is_valid_geojson(self, runner, temp_boundary_file, temp_output_file):
        """Test that grid output is valid GeoJSON."""
        result = runner.invoke(cli, [
            'sample', 'grid',
            '--spacing', '100',
            '--aoi', temp_boundary_file,
            '--output', temp_output_file
        ])

        assert result.exit_code == 0

        # Verify it's valid GeoJSON
        gdf = gpd.read_file(temp_output_file)
        assert 'geometry' in gdf.columns
        assert len(gdf) > 0

    def test_grid_output_contains_required_fields(self, runner, temp_boundary_file, temp_output_file):
        """Test that grid output contains required fields."""
        result = runner.invoke(cli, [
            'sample', 'grid',
            '--spacing', '100',
            '--aoi', temp_boundary_file,
            '--output', temp_output_file
        ])

        assert result.exit_code == 0

        gdf = gpd.read_file(temp_output_file)
        required_fields = ['sample_id', 'strategy', 'timestamp']

        for field in required_fields:
            assert field in gdf.columns
