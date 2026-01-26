"""
SpatialSamplingPro Metadata Management Module

This module provides comprehensive metadata management for sampling protocols,
ensuring complete traceability, reproducibility, and documentation.

Main components:
- Models: Data structures for metadata
- Serializer: Save/load metadata in multiple formats
- Validator: Validate metadata completeness and correctness
- Exporter: Export to various output formats

Example usage:
    >>> from ssp.metadata import (
    ...     SamplingMetadata,
    ...     MetadataSerializer,
    ...     MetadataValidator,
    ...     MetadataExporter
    ... )
    >>>
    >>> # Create metadata from strategy
    >>> metadata = SamplingMetadata.create_from_strategy(
    ...     strategy=grid_strategy,
    ...     boundary=boundary,
    ...     protocol_name="My Study",
    ...     description="Sampling protocol for spatial study"
    ... )
    >>>
    >>> # Validate metadata
    >>> validator = MetadataValidator()
    >>> is_valid, errors = validator.validate(metadata)
    >>>
    >>> # Export to multiple formats
    >>> exporter = MetadataExporter()
    >>> exporter.export_all(
    ...     metadata,
    ...     points_gdf,
    ...     output_dir="exports/",
    ...     base_name="my_study"
    ... )
"""

from ssp.metadata.models import (
    SamplingMetadata,
    SamplingStrategyType,
    BoundaryMetadata,
    SamplingParametersMetadata,
    ExecutionMetadata,
    DataSourceMetadata,
    ResultsMetadata
)

from ssp.metadata.serializer import (
    MetadataSerializer,
    MetadataBatchSerializer
)

from ssp.metadata.validator import (
    MetadataValidator,
    MetadataValidationError,
    quick_validate
)

from ssp.metadata.exporter import (
    MetadataExporter
)

__all__ = [
    # Models
    'SamplingMetadata',
    'SamplingStrategyType',
    'BoundaryMetadata',
    'SamplingParametersMetadata',
    'ExecutionMetadata',
    'DataSourceMetadata',
    'ResultsMetadata',

    # Serializer
    'MetadataSerializer',
    'MetadataBatchSerializer',

    # Validator
    'MetadataValidator',
    'MetadataValidationError',
    'quick_validate',

    # Exporter
    'MetadataExporter',
]
