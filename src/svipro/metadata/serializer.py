"""
Metadata Serializer Module

Handles serialization and deserialization of sampling metadata
to and from various formats (JSON, YAML, GeoJSON).

This module ensures metadata can be easily stored, loaded, and
transmitted between different systems and researchers.
"""

import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

from svipro.metadata.models import SamplingMetadata


class MetadataSerializer:
    """
    Serializer for sampling metadata.

    Supports multiple formats including JSON, YAML, and GeoJSON.
    Handles proper encoding of metadata fields and ensures compatibility
    with external tools and workflows.

    Example:
        >>> metadata = SamplingMetadata(...)
        >>> serializer = MetadataSerializer()
        >>> serializer.to_json(metadata, "protocol.json")
        >>> loaded = serializer.from_json("protocol.json")
    """

    def __init__(self, format: str = 'json'):
        """
        Initialize serializer.

        Args:
            format: Output format ('json', 'yaml', or 'geojson').
        """
        self.format = format.lower()

        if self.format not in ['json', 'yaml', 'geojson']:
            raise ValueError(
                f"Unsupported format: {format}. "
                "Supported formats: 'json', 'yaml', 'geojson'"
            )

    def to_json(
        self,
        metadata: SamplingMetadata,
        filepath: Optional[str] = None,
        pretty: bool = True
    ) -> str:
        """
        Serialize metadata to JSON format.

        Args:
            metadata: SamplingMetadata instance to serialize.
            filepath: Optional file path to save JSON. If None, returns string.
            pretty: If True, formats JSON with indentation.

        Returns:
            JSON string if filepath is None, otherwise None (writes to file).

        Raises:
            IOError: If filepath cannot be written.
            ValueError: If metadata is invalid.
        """
        data = metadata.to_dict()

        if pretty:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            json_str = json.dumps(data, ensure_ascii=False)

        if filepath:
            try:
                Path(filepath).write_text(json_str, encoding='utf-8')
            except Exception as e:
                raise IOError(f"Failed to write JSON to {filepath}: {e}")
        else:
            return json_str

    def from_json(self, source: str) -> SamplingMetadata:
        """
        Deserialize metadata from JSON format.

        Args:
            source: JSON file path or JSON string.

        Returns:
            SamplingMetadata instance.

        Raises:
            IOError: If file cannot be read.
            ValueError: If JSON is invalid or metadata is malformed.
        """
        try:
            # Check if source is a file path or JSON string
            if Path(source).exists():
                json_str = Path(source).read_text(encoding='utf-8')
            else:
                json_str = source
        except (OSError, IOError):
            # Not a file path, treat as JSON string
            json_str = source

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        return SamplingMetadata.from_dict(data)

    def to_yaml(
        self,
        metadata: SamplingMetadata,
        filepath: Optional[str] = None,
        flow_style: bool = False
    ) -> str:
        """
        Serialize metadata to YAML format.

        Args:
            metadata: SamplingMetadata instance to serialize.
            filepath: Optional file path to save YAML. If None, returns string.
            flow_style: If True, uses flow style (more compact).

        Returns:
            YAML string if filepath is None, otherwise None (writes to file).

        Raises:
            IOError: If filepath cannot be written.
            ValueError: If metadata is invalid.
        """
        data = metadata.to_dict()

        try:
            yaml_str = yaml.dump(
                data,
                default_flow_style=flow_style,
                allow_unicode=True,
                sort_keys=False
            )
        except Exception as e:
            raise ValueError(f"Failed to convert to YAML: {e}")

        if filepath:
            try:
                Path(filepath).write_text(yaml_str, encoding='utf-8')
            except Exception as e:
                raise IOError(f"Failed to write YAML to {filepath}: {e}")
        else:
            return yaml_str

    def from_yaml(self, source: str) -> SamplingMetadata:
        """
        Deserialize metadata from YAML format.

        Args:
            source: YAML file path or YAML string.

        Returns:
            SamplingMetadata instance.

        Raises:
            IOError: If file cannot be read.
            ValueError: If YAML is invalid or metadata is malformed.
        """
        try:
            # Check if source is a file path or YAML string
            if Path(source).exists():
                yaml_str = Path(source).read_text(encoding='utf-8')
            else:
                yaml_str = source
        except (OSError, IOError):
            # Not a file path, treat as YAML string
            yaml_str = source

        try:
            data = yaml.safe_load(yaml_str)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")

        if not isinstance(data, dict):
            raise ValueError("YAML must contain a dictionary at top level")

        return SamplingMetadata.from_dict(data)

    def to_geojson(
        self,
        metadata: SamplingMetadata,
        points_gdf: Any,
        filepath: str
    ) -> None:
        """
        Serialize metadata and sample points to GeoJSON format.

        Creates a GeoJSON FeatureCollection with metadata embedded
        in the FeatureCollection properties.

        Args:
            metadata: SamplingMetadata instance.
            points_gdf: GeoDataFrame with sample points.
            filepath: Output GeoJSON file path.

        Raises:
            IOError: If file cannot be written.
            ValueError: If metadata or points are invalid.
        """
        try:
            from geojson import Feature, FeatureCollection, dump
            import geopandas as gpd
        except ImportError as e:
            raise ImportError(
                f"Required library for GeoJSON export not available: {e}"
            )

        if not isinstance(points_gdf, gpd.GeoDataFrame):
            raise ValueError(
                f"points_gdf must be GeoDataFrame, got {type(points_gdf)}"
            )

        # Convert points to features
        features = []
        for _, row in points_gdf.iterrows():
            feature = Feature(
                geometry=row['geometry'].__geo_interface__,
                properties=row.drop('geometry').to_dict()
            )
            features.append(feature)

        # Add metadata to FeatureCollection properties
        collection = FeatureCollection(
            features,
            properties=metadata.to_dict()
        )

        try:
            with open(filepath, 'w') as f:
                dump(collection, f)
        except Exception as e:
            raise IOError(f"Failed to write GeoJSON to {filepath}: {e}")

    def serialize(
        self,
        metadata: SamplingMetadata,
        filepath: str,
        **kwargs
    ) -> None:
        """
        Serialize metadata using the configured format.

        Args:
            metadata: SamplingMetadata instance to serialize.
            filepath: Output file path.
            **kwargs: Additional format-specific arguments.

        Raises:
            ValueError: If format is not supported.
            IOError: If file cannot be written.
        """
        if self.format == 'json':
            self.to_json(metadata, filepath, **kwargs)
        elif self.format == 'yaml':
            self.to_yaml(metadata, filepath, **kwargs)
        elif self.format == 'geojson':
            if 'points_gdf' not in kwargs:
                raise ValueError(
                    "points_gdf required for GeoJSON format"
                )
            self.to_geojson(metadata, kwargs['points_gdf'], filepath)
        else:
            raise ValueError(f"Unsupported format: {self.format}")

    def deserialize(self, source: str) -> SamplingMetadata:
        """
        Deserialize metadata using the configured format.

        Args:
            source: File path or string to deserialize from.

        Returns:
            SamplingMetadata instance.

        Raises:
            ValueError: If format is not supported or data is invalid.
            IOError: If file cannot be read.
        """
        if self.format in ['json', 'geojson']:
            return self.from_json(source)
        elif self.format == 'yaml':
            return self.from_yaml(source)
        else:
            raise ValueError(f"Unsupported format: {self.format}")


class MetadataBatchSerializer:
    """
    Batch serializer for multiple metadata files.

    Useful for processing multiple protocols or creating
    metadata archives.

    Example:
        >>> batch = MetadataBatchSerializer()
        >>> batch.add_metadata(protocol1, "protocol1.json")
        >>> batch.add_metadata(protocol2, "protocol2.json")
        >>> batch.write_all()
    """

    def __init__(self):
        """Initialize batch serializer."""
        self.queue: list = []

    def add(
        self,
        metadata: SamplingMetadata,
        filepath: str,
        format: str = 'json'
    ) -> None:
        """
        Add metadata to serialization queue.

        Args:
            metadata: SamplingMetadata to serialize.
            filepath: Output file path.
            format: Output format ('json' or 'yaml').
        """
        self.queue.append({
            'metadata': metadata,
            'filepath': filepath,
            'format': format
        })

    def write_all(self) -> None:
        """
        Write all queued metadata to files.

        Raises:
            IOError: If any file cannot be written.
        """
        errors = []

        for item in self.queue:
            try:
                serializer = MetadataSerializer(format=item['format'])
                serializer.serialize(
                    item['metadata'],
                    item['filepath']
                )
            except Exception as e:
                errors.append(f"{item['filepath']}: {e}")

        if errors:
            raise IOError(
                f"Failed to write {len(errors)} file(s):\n" +
                "\n".join(errors)
            )

    def clear(self) -> None:
        """Clear the serialization queue."""
        self.queue.clear()

    def __len__(self) -> int:
        """Return number of items in queue."""
        return len(self.queue)
