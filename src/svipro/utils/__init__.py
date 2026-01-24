"""
Utility modules for SVIPro.

This package contains various utility functions and helpers for
spatial operations, validation, and edge case handling.
"""

from svipro.utils.edge_cases import (
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

__all__ = [
    'handle_small_boundary',
    'fix_invalid_geometry',
    'ensure_polygon',
    'validate_crs_compatibility',
    'handle_empty_geodataframe',
    'warn_large_output',
    'estimate_processing_time',
    'check_spacing_bounds',
    'safe_geometry_operation'
]
