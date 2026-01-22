"""
Metadata Validator Module

Validates sampling metadata for completeness, correctness, and consistency.

This module ensures that metadata meets quality standards and contains
all required information for reproducibility.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from svipro.metadata.models import SamplingMetadata


class MetadataValidationError(Exception):
    """Exception raised when metadata validation fails."""
    pass


class MetadataValidator:
    """
    Validator for sampling metadata.

    Performs comprehensive validation of metadata including:
    - Required field presence
    - Data type correctness
    - Value ranges and formats
    - Consistency checks
    - Best practices compliance

    Example:
        >>> validator = MetadataValidator()
        >>> metadata = SamplingMetadata(...)
        >>> is_valid, errors = validator.validate(metadata)
        >>> if not is_valid:
        ...     print("Validation errors:", errors)
    """

    def __init__(self, strict: bool = False):
        """
        Initialize validator.

        Args:
            strict: If True, validation fails on warnings. If False,
                   only fails on errors.
        """
        self.strict = strict
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, metadata: SamplingMetadata) -> tuple[bool, List[str]]:
        """
        Validate metadata completely.

        Args:
            metadata: SamplingMetadata instance to validate.

        Returns:
            Tuple of (is_valid, error_messages).
            is_valid is False if errors found (warnings don't affect it).
        """
        self.errors.clear()
        self.warnings.clear()

        # Validate top-level fields
        self._validate_top_level(metadata)

        # Validate boundary metadata
        if metadata.boundary:
            self._validate_boundary(metadata.boundary)

        # Validate parameters metadata
        if metadata.parameters:
            self._validate_parameters(metadata.parameters)

        # Validate execution metadata
        if metadata.execution:
            self._validate_execution(metadata.execution)

        # Validate data sources
        for idx, ds in enumerate(metadata.data_sources):
            self._validate_data_source(ds, idx)

        # Validate results metadata
        if metadata.results:
            self._validate_results(metadata.results)

        # Validate consistency
        self._validate_consistency(metadata)

        # In strict mode, warnings become errors
        if self.strict:
            self.errors.extend(self.warnings)
            self.warnings.clear()

        return (len(self.errors) == 0, self.errors + self.warnings)

    def _validate_top_level(self, metadata: SamplingMetadata) -> None:
        """Validate top-level metadata fields."""
        required_fields = {
            'protocol_id': str,
            'protocol_name': str,
            'description': str,
            'version': str,
            'created_at': str
        }

        for field, expected_type in required_fields.items():
            value = getattr(metadata, field, None)

            if value is None:
                self.errors.append(f"Missing required field: {field}")
            elif not isinstance(value, expected_type):
                self.errors.append(
                    f"Field '{field}' must be {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )

        # Validate protocol_id format
        if metadata.protocol_id:
            if not re.match(r'^[a-zA-Z0-9_\-]+$', metadata.protocol_id):
                self.errors.append(
                    f"protocol_id must contain only alphanumeric characters, "
                    f"underscores, and hyphens: '{metadata.protocol_id}'"
                )

        # Validate version format (semantic versioning)
        if metadata.version:
            if not re.match(r'^\d+\.\d+\.\d+', metadata.version):
                self.warnings.append(
                    f"version should follow semantic versioning (e.g., '1.0.0'): "
                    f"'{metadata.version}'"
                )

        # Validate timestamp format
        if metadata.created_at:
            try:
                datetime.fromisoformat(metadata.created_at.replace('Z', '+00:00'))
            except ValueError:
                self.errors.append(
                    f"created_at must be ISO 8601 format: '{metadata.created_at}'"
                )

    def _validate_boundary(self, boundary: Any) -> None:
        """Validate boundary metadata."""
        required_fields = ['geometry_wkt', 'crs', 'area_km2', 'bounds']

        for field in required_fields:
            if not hasattr(boundary, field) or getattr(boundary, field) is None:
                self.errors.append(f"boundary missing required field: {field}")

        # Validate CRS format
        if hasattr(boundary, 'crs') and boundary.crs:
            if not boundary.crs.upper().startswith('EPSG:'):
                self.warnings.append(
                    f"boundary.crs should be EPSG format (e.g., 'EPSG:4326'): "
                    f"'{boundary.crs}'"
                )

        # Validate area is positive
        if hasattr(boundary, 'area_km2') and boundary.area_km2 is not None:
            if boundary.area_km2 <= 0:
                self.errors.append(
                    f"boundary.area_km2 must be positive: {boundary.area_km2}"
                )

        # Validate bounds has 4 elements
        if hasattr(boundary, 'bounds') and boundary.bounds is not None:
            if len(boundary.bounds) != 4:
                self.errors.append(
                    f"boundary.bounds must have 4 elements (minx, miny, maxx, maxy): "
                    f"got {len(boundary.bounds)}"
                )

    def _validate_parameters(self, params: Any) -> None:
        """Validate sampling parameters metadata."""
        required_fields = ['spacing', 'seed', 'crs', 'strategy_type']

        for field in required_fields:
            if not hasattr(params, field) or getattr(params, field) is None:
                self.errors.append(f"parameters missing required field: {field}")

        # Validate spacing is positive
        if hasattr(params, 'spacing') and params.spacing is not None:
            if params.spacing <= 0:
                self.errors.append(
                    f"parameters.spacing must be positive: {params.spacing}"
                )

        # Validate seed is non-negative
        if hasattr(params, 'seed') and params.seed is not None:
            if params.seed < 0:
                self.errors.append(
                    f"parameters.seed must be non-negative: {params.seed}"
                )

        # Validate strategy_type is known
        if hasattr(params, 'strategy_type') and params.strategy_type:
            valid_strategies = [
                'grid_sampling',
                'road_network_sampling',
                'optimized_coverage',
                'stratified_random'
            ]
            if params.strategy_type not in valid_strategies:
                self.warnings.append(
                    f"parameters.strategy_type '{params.strategy_type}' is not a "
                    f"recognized strategy type: {valid_strategies}"
                )

    def _validate_execution(self, execution: Any) -> None:
        """Validate execution metadata."""
        required_fields = ['timestamp', 'python_version', 'svipro_version']

        for field in required_fields:
            if not hasattr(execution, field) or getattr(execution, field) is None:
                self.errors.append(f"execution missing required field: {field}")

        # Validate timestamp format
        if hasattr(execution, 'timestamp') and execution.timestamp:
            try:
                datetime.fromisoformat(execution.timestamp.replace('Z', '+00:00'))
            except ValueError:
                self.errors.append(
                    f"execution.timestamp must be ISO 8601 format: "
                    f"'{execution.timestamp}'"
                )

        # Validate runtime is non-negative
        if hasattr(execution, 'runtime_seconds') and execution.runtime_seconds is not None:
            if execution.runtime_seconds < 0:
                self.errors.append(
                    f"execution.runtime_seconds must be non-negative: "
                    f"{execution.runtime_seconds}"
                )

    def _validate_data_source(self, ds: Any, idx: int) -> None:
        """Validate data source metadata."""
        required_fields = ['source_type']

        for field in required_fields:
            if not hasattr(ds, field) or getattr(ds, field) is None:
                self.errors.append(
                    f"data_sources[{idx}] missing required field: {field}"
                )

        # Validate timestamp format if present
        if hasattr(ds, 'access_timestamp') and ds.access_timestamp:
            try:
                datetime.fromisoformat(ds.access_timestamp.replace('Z', '+00:00'))
            except ValueError:
                self.errors.append(
                    f"data_sources[{idx}].access_timestamp must be ISO 8601 format: "
                    f"'{ds.access_timestamp}'"
                )

    def _validate_results(self, results: Any) -> None:
        """Validate results metadata."""
        required_fields = ['n_points', 'density_pts_per_km2']

        for field in required_fields:
            if not hasattr(results, field) or getattr(results, field) is None:
                self.errors.append(f"results missing required field: {field}")

        # Validate n_points is non-negative
        if hasattr(results, 'n_points') and results.n_points is not None:
            if results.n_points < 0:
                self.errors.append(
                    f"results.n_points must be non-negative: {results.n_points}"
                )

        # Validate density is non-negative
        if hasattr(results, 'density_pts_per_km2') and results.density_pts_per_km2 is not None:
            if results.density_pts_per_km2 < 0:
                self.errors.append(
                    f"results.density_pts_per_km2 must be non-negative: "
                    f"{results.density_pts_per_km2}"
                )

    def _validate_consistency(self, metadata: SamplingMetadata) -> None:
        """Validate consistency across metadata fields."""
        # Check CRS consistency
        crs_values = []

        if metadata.boundary and hasattr(metadata.boundary, 'crs'):
            crs_values.append(metadata.boundary.crs)

        if metadata.parameters and hasattr(metadata.parameters, 'crs'):
            crs_values.append(metadata.parameters.crs)

        if len(crs_values) > 1:
            if len(set(crs_values)) > 1:
                self.warnings.append(
                    f"CRS values are inconsistent across metadata: {crs_values}"
                )

        # Check timestamp ordering
        if metadata.created_at and metadata.execution and metadata.execution.timestamp:
            try:
                created = datetime.fromisoformat(metadata.created_at.replace('Z', '+00:00'))
                exec_time = datetime.fromisoformat(metadata.execution.timestamp.replace('Z', '+00:00'))

                if exec_time < created:
                    self.warnings.append(
                        f"execution.timestamp ({metadata.execution.timestamp}) "
                        f"is before created_at ({metadata.created_at})"
                    )
            except ValueError:
                # Already caught by timestamp validation
                pass

        # Check results consistency
        if metadata.results and metadata.parameters:
            if (metadata.results.n_points == 0 and
                hasattr(metadata.parameters, 'spacing') and
                metadata.parameters.spacing > 0):
                self.warnings.append(
                    "results.n_points is 0 but positive spacing was specified. "
                    "This may indicate the sampling failed."
                )

    def validate_dict(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate metadata from dictionary.

        Args:
            data: Dictionary containing metadata.

        Returns:
            Tuple of (is_valid, error_messages).
        """
        try:
            metadata = SamplingMetadata.from_dict(data)
            return self.validate(metadata)
        except Exception as e:
            return (False, [f"Failed to create metadata from dict: {e}"])

    def validate_file(self, filepath: str, format: str = 'json') -> tuple[bool, List[str]]:
        """
        Validate metadata from file.

        Args:
            filepath: Path to metadata file.
            format: File format ('json' or 'yaml').

        Returns:
            Tuple of (is_valid, error_messages).
        """
        try:
            from svipro.metadata.serializer import MetadataSerializer

            serializer = MetadataSerializer(format=format)
            metadata = serializer.deserialize(filepath)
            return self.validate(metadata)
        except Exception as e:
            return (False, [f"Failed to load metadata from file: {e}"])


def quick_validate(metadata: SamplingMetadata) -> bool:
    """
    Quick validation check (errors only, no warnings).

    Convenience function for simple validation.

    Args:
        metadata: SamplingMetadata to validate.

    Returns:
        True if valid, False otherwise.
    """
    validator = MetadataValidator(strict=False)
    is_valid, _ = validator.validate(metadata)
    return is_valid
