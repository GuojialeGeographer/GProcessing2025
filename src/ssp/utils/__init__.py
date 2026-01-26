"""
Utility modules for SpatialSamplingPro.

This package contains various utility functions and helpers for
spatial operations, validation, and edge case handling.
"""

from ssp.utils.edge_cases import (
    handle_small_boundary,
    fix_invalid_geometry,
    ensure_polygon,
    validate_crs_compatibility,
    handle_empty_geodataframe,
    warn_large_output,
    estimate_processing_time,
    check_spacing_bounds,
    safe_geometry_operation
)

from ssp.utils.coordinates import (
    meters_to_degrees,
    degrees_to_meters,
    estimate_center_latitude,
    convert_spacing_for_crs
)

__all__ = [
    'handle_small_boundary',
    'fix_invalid_geometry',
    'ensure_polygon',
    'validate_crs_compatibility',
    'handle_empty_geodataframe',
    'warn_large_output',
    'estimate_processing_time',
    'check_spacing_bounds',
    'safe_geometry_operation',
    'meters_to_degrees',
    'degrees_to_meters',
    'estimate_center_latitude',
    'convert_spacing_for_crs'
]
