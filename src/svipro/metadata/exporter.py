"""
Metadata Exporter Module

Exports sampling metadata and sample points to various formats
for use in different applications and workflows.

Supported formats:
- GeoJSON (with embedded metadata)
- YAML (protocol files)
- CSV (metadata summary)
- HTML (human-readable reports)
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
import csv

from svipro.metadata.models import SamplingMetadata
from svipro.metadata.serializer import MetadataSerializer


class MetadataExporter:
    """
    Exporter for sampling metadata and sample points.

    Provides unified interface for exporting to multiple formats
    with appropriate metadata inclusion.

    Example:
        >>> exporter = MetadataExporter()
        >>> exporter.export_geojson(metadata, points, "output.geojson")
        >>> exporter.export_yaml(metadata, "protocol.yaml")
        >>> exporter.export_csv(metadata, "summary.csv")
    """

    def __init__(self):
        """Initialize exporter."""
        self.serializer = MetadataSerializer()

    def export_geojson(
        self,
        metadata: SamplingMetadata,
        points_gdf: Any,
        filepath: str,
        pretty: bool = True
    ) -> None:
        """
        Export metadata and sample points to GeoJSON format.

        GeoJSON is ideal for:
        - GIS software (QGIS, ArcGIS)
        - Web mapping applications
        - Data interchange

        Args:
            metadata: SamplingMetadata instance.
            points_gdf: GeoDataFrame with sample points.
            filepath: Output GeoJSON file path.
            pretty: If True, formats JSON with indentation.

        Raises:
            IOError: If file cannot be written.
            ValueError: If inputs are invalid.
        """
        try:
            self.serializer.to_geojson(metadata, points_gdf, filepath)
        except Exception as e:
            raise IOError(f"Failed to export GeoJSON: {e}")

    def export_yaml(
        self,
        metadata: SamplingMetadata,
        filepath: str,
        include_results: bool = True
    ) -> None:
        """
        Export metadata to YAML protocol file.

        YAML format is ideal for:
        - Human-readable protocols
        - Version control (Git)
        - Configuration files

        Args:
            metadata: SamplingMetadata instance.
            filepath: Output YAML file path.
            include_results: If True, includes results section.

        Raises:
            IOError: If file cannot be written.
        """
        # Create a copy of metadata
        export_data = metadata.to_dict()

        # Optionally remove results (for protocol files before execution)
        if not include_results and 'results' in export_data:
            del export_data['results']

        try:
            # Use yaml serializer directly
            yaml_serializer = MetadataSerializer(format='yaml')
            yaml_serializer.to_yaml(metadata, filepath)
        except Exception as e:
            raise IOError(f"Failed to export YAML: {e}")

    def export_json(
        self,
        metadata: SamplingMetadata,
        filepath: str,
        pretty: bool = True
    ) -> None:
        """
        Export metadata to JSON format.

        JSON format is ideal for:
        - Machine-readable protocols
        - Web applications
        - Data interchange

        Args:
            metadata: SamplingMetadata instance.
            filepath: Output JSON file path.
            pretty: If True, formats JSON with indentation.

        Raises:
            IOError: If file cannot be written.
        """
        try:
            json_serializer = MetadataSerializer(format='json')
            json_serializer.to_json(metadata, filepath, pretty=pretty)
        except Exception as e:
            raise IOError(f"Failed to export JSON: {e}")

    def export_csv(
        self,
        metadata: SamplingMetadata,
        filepath: str,
        include_nested: bool = False
    ) -> None:
        """
        Export metadata summary to CSV format.

        CSV format is ideal for:
        - Spreadsheet applications (Excel)
        - Data analysis
        - Quick summaries

        Args:
            metadata: SamplingMetadata instance.
            filepath: Output CSV file path.
            include_nested: If True, includes nested fields as JSON strings.

        Raises:
            IOError: If file cannot be written.
        """
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow(['Field', 'Value'])

                # Write top-level fields
                data = metadata.to_dict()

                # Flatten nested fields
                flat_data = self._flatten_dict(data, include_nested)

                for key, value in flat_data.items():
                    writer.writerow([key, str(value)])

        except Exception as e:
            raise IOError(f"Failed to export CSV: {e}")

    def _flatten_dict(
        self,
        data: Dict[str, Any],
        include_nested: bool,
        prefix: str = ''
    ) -> Dict[str, str]:
        """
        Flatten nested dictionary for CSV export.

        Args:
            data: Dictionary to flatten.
            include_nested: If True, includes nested dicts as JSON strings.
            prefix: Current key prefix (for recursion).

        Returns:
            Flattened dictionary.
        """
        flat = {}

        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if value is None:
                flat[full_key] = ''
            elif isinstance(value, (int, float, str, bool)):
                flat[full_key] = str(value)
            elif isinstance(value, list):
                if include_nested and value:
                    # Convert list to JSON string
                    import json
                    flat[full_key] = json.dumps(value)
                else:
                    flat[full_key] = f"[{len(value)} items]"
            elif isinstance(value, dict):
                if include_nested:
                    # Convert dict to JSON string
                    import json
                    flat[full_key] = json.dumps(value)
                else:
                    # Recursively flatten
                    flat.update(self._flatten_dict(value, include_nested, full_key))
            else:
                flat[full_key] = str(value)

        return flat

    def export_html_report(
        self,
        metadata: SamplingMetadata,
        filepath: str,
        include_plots: bool = False
    ) -> None:
        """
        Export metadata as HTML report.

        HTML format is ideal for:
        - Human-readable reports
        - Web sharing
        - Documentation

        Args:
            metadata: SamplingMetadata instance.
            filepath: Output HTML file path.
            include_plots: If True, includes placeholder for plots.

        Raises:
            IOError: If file cannot be written.
        """
        html_content = self._generate_html_report(metadata, include_plots)

        try:
            Path(filepath).write_text(html_content, encoding='utf-8')
        except Exception as e:
            raise IOError(f"Failed to export HTML report: {e}")

    def _generate_html_report(
        self,
        metadata: SamplingMetadata,
        include_plots: bool
    ) -> str:
        """Generate HTML content for report."""
        data = metadata.to_dict()

        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SVIPro Sampling Protocol Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; }
        h2 { color: #34495e; margin-top: 30px; }
        .metadata-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .metadata-table th, .metadata-table td {
            border: 1px solid #ddd; padding: 12px; text-align: left;
        }
        .metadata-table th { background-color: #3498db; color: white; }
        .metadata-table tr:nth-child(even) { background-color: #f2f2f2; }
        .section { margin: 30px 0; }
        .label { font-weight: bold; color: #2c3e50; }
        .value { color: #34495e; }
        .footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd;
                  color: #7f8c8d; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>📍 SVIPro Sampling Protocol Report</h1>
"""

        # Protocol info
        html += f"""
    <div class="section">
        <h2>Protocol Information</h2>
        <table class="metadata-table">
            <tr><th>Field</th><th>Value</th></tr>
            <tr><td class="label">Protocol ID</td><td class="value">{data.get('protocol_id', 'N/A')}</td></tr>
            <tr><td class="label">Protocol Name</td><td class="value">{data.get('protocol_name', 'N/A')}</td></tr>
            <tr><td class="label">Description</td><td class="value">{data.get('description', 'N/A')}</td></tr>
            <tr><td class="label">Version</td><td class="value">{data.get('version', 'N/A')}</td></tr>
            <tr><td class="label">Created At</td><td class="value">{data.get('created_at', 'N/A')}</td></tr>
            <tr><td class="label">Author</td><td class="value">{data.get('author', 'N/A')}</td></tr>
            <tr><td class="label">Institution</td><td class="value">{data.get('institution', 'N/A')}</td></tr>
            <tr><td class="label">Contact</td><td class="value">{data.get('contact', 'N/A')}</td></tr>
        </table>
    </div>
"""

        # Boundary info
        if data.get('boundary'):
            b = data['boundary']
            html += f"""
    <div class="section">
        <h2>Boundary Information</h2>
        <table class="metadata-table">
            <tr><th>Field</th><th>Value</th></tr>
            <tr><td class="label">CRS</td><td class="value">{b.get('crs', 'N/A')}</td></tr>
            <tr><td class="label">Area</td><td class="value">{b.get('area_km2', 'N/A')} km²</td></tr>
            <tr><td class="label">Bounds</td><td class="value">{b.get('bounds', 'N/A')}</td></tr>
            <tr><td class="label">Source</td><td class="value">{b.get('source', 'N/A')}</td></tr>
            <tr><td class="label">Description</td><td class="value">{b.get('description', 'N/A')}</td></tr>
        </table>
    </div>
"""

        # Parameters info
        if data.get('parameters'):
            p = data['parameters']
            html += f"""
    <div class="section">
        <h2>Sampling Parameters</h2>
        <table class="metadata-table">
            <tr><th>Field</th><th>Value</th></tr>
            <tr><td class="label">Strategy Type</td><td class="value">{p.get('strategy_type', 'N/A')}</td></tr>
            <tr><td class="label">Spacing</td><td class="value">{p.get('spacing', 'N/A')} m</td></tr>
            <tr><td class="label">Seed</td><td class="value">{p.get('seed', 'N/A')}</td></tr>
            <tr><td class="label">CRS</td><td class="value">{p.get('crs', 'N/A')}</td></tr>
        </table>
    </div>
"""

        # Results info
        if data.get('results'):
            r = data['results']
            html += f"""
    <div class="section">
        <h2>Results Summary</h2>
        <table class="metadata-table">
            <tr><th>Field</th><th>Value</th></tr>
            <tr><td class="label">Number of Points</td><td class="value">{r.get('n_points', 'N/A')}</td></tr>
            <tr><td class="label">Density</td><td class="value">{r.get('density_pts_per_km2', 'N/A')} pts/km²</td></tr>
        </table>
    </div>
"""

        # Footer
        execution = data.get('execution') or {}
        svipro_version = execution.get('svipro_version', '0.1.0') if isinstance(execution, dict) else '0.1.0'
        html += f"""
    <div class="footer">
        <p>Generated by SVIPro v{svipro_version}</p>
        <p>For more information: https://github.com/GuojialeGeographer/GProcessing2025</p>
    </div>
</body>
</html>
"""
        return html

    def export_all(
        self,
        metadata: SamplingMetadata,
        points_gdf: Any,
        output_dir: str,
        base_name: str
    ) -> Dict[str, str]:
        """
        Export metadata to all supported formats.

        Creates a complete package with all export formats.

        Args:
            metadata: SamplingMetadata instance.
            points_gdf: GeoDataFrame with sample points.
            output_dir: Directory to save files.
            base_name: Base name for output files (without extension).

        Returns:
            Dictionary mapping format to filepath.

        Raises:
            IOError: If any file cannot be written.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        exported_files = {}

        # Export to GeoJSON
        geojson_path = output_path / f"{base_name}.geojson"
        self.export_geojson(metadata, points_gdf, str(geojson_path))
        exported_files['geojson'] = str(geojson_path)

        # Export to YAML
        yaml_path = output_path / f"{base_name}_protocol.yaml"
        self.export_yaml(metadata, str(yaml_path))
        exported_files['yaml'] = str(yaml_path)

        # Export to JSON
        json_path = output_path / f"{base_name}_metadata.json"
        self.export_json(metadata, str(json_path))
        exported_files['json'] = str(json_path)

        # Export to CSV
        csv_path = output_path / f"{base_name}_summary.csv"
        self.export_csv(metadata, str(csv_path))
        exported_files['csv'] = str(csv_path)

        # Export to HTML
        html_path = output_path / f"{base_name}_report.html"
        self.export_html_report(metadata, str(html_path))
        exported_files['html'] = str(html_path)

        return exported_files
