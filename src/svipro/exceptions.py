"""
Custom exceptions for SVIPro package.

This module defines all custom exceptions used throughout the SVIPro package,
providing clear, user-friendly error messages and proper error categorization.
"""

from typing import Optional, Any, Dict


class SVIProError(Exception):
    """
    Base exception class for all SVIPro errors.

    All custom exceptions in SVIPro inherit from this base class,
    allowing users to catch all SVIPro-specific errors with a single
    except clause.

    Attributes:
        message: Human-readable error description
        details: Optional dictionary with additional error context

    Example:
        >>> try:
        ...     strategy.generate(boundary)
        ... except SVIProError as e:
        ...     print(f"SVIPro error: {e}")
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize SVIPro error.

        Args:
            message: Human-readable error description
            details: Optional dictionary with additional context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return error message."""
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/debugging."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'details': self.details
        }


class ConfigurationError(SVIProError):
    """
    Raised when configuration parameters are invalid.

    This includes invalid spacing, CRS, seed values, or other
    configuration-related issues.

    Example:
        >>> raise ConfigurationError(
        ...     "Invalid spacing value",
        ...     details={'spacing': -10, 'valid_range': '(0, inf)'}
        ... )
    """

    pass


class BoundaryError(SVIProError):
    """
    Raised when the area of interest (boundary) is invalid.

    This includes:
    - Invalid geometry (self-intersections, etc.)
    - Empty or zero-area polygons
    - Boundary too small for the given spacing
    - Boundary in unsupported coordinate systems

    Example:
        >>> raise BoundaryError(
        ...     "Boundary area too small for specified spacing",
        ...     details={'area_km2': 0.001, 'spacing_m': 100}
        ... )
    """

    pass


class SamplingError(SVIProError):
    """
    Raised when sampling operation fails.

    This includes:
    - No sample points generated
    - Sampling algorithm failures
    - Edge cases during point generation

    Example:
        >>> raise SamplingError(
        ...     "No sample points could be generated within boundary",
        ...     details={'n_edges': 0, 'boundary_area': 1.5}
        ... )
    """

    pass


class NetworkDownloadError(SVIProError):
    """
    Raised when OSM network download fails.

    This includes:
    - Network connectivity issues
    - OSM server errors
    - Invalid boundary for network query
    - No network data available for area

    Example:
        >>> raise NetworkDownloadError(
        ...     "Failed to download road network from OpenStreetMap",
        ...     details={'network_type': 'drive', 'timeout_seconds': 30}
        ... )
    """

    pass


class ValidationError(SVIProError):
    """
    Raised when input validation fails.

    This includes:
    - Invalid file formats
    - Missing required fields
    - Type mismatches
    - Value out of range

    Example:
        >>> raise ValidationError(
        ...     "Invalid GeoJSON file",
        ...     details={'file': 'data.geojson', 'reason': 'no geometry column'}
        ... )
    """

    pass


class ExportError(SVIProError):
    """
    Raised when data export fails.

    This includes:
    - File write permissions
    - Invalid output paths
    - Serialization errors
    - Disk space issues

    Example:
        >>> raise ExportError(
        ...     "Failed to write GeoJSON file",
        ...     details={'filepath': '/protected/output.geojson'}
        ... )
    """

    pass


class VisualizationError(SVIProError):
    """
    Raised when visualization operations fail.

    This includes:
    - Missing visualization dependencies
    - Invalid plotting parameters
    - Rendering errors

    Example:
        >>> raise VisualizationError(
        ...     "Failed to create map",
        ...     details={'reason': 'folium not installed'}
        ... )
    """

    pass


def format_error_context(error: Exception, include_traceback: bool = False) -> str:
    """
    Format error with context for user-friendly display.

    Args:
        error: The exception to format
        include_traceback: Whether to include stack trace

    Returns:
        Formatted error message string

    Example:
        >>> try:
        ...     raise ConfigurationError("Invalid spacing", {'spacing': -10})
        ... except SVIProError as e:
        ...     print(format_error_context(e))
    """
    lines = [f"❌ Error: {error}"]

    if isinstance(error, SVIProError) and error.details:
        lines.append("\n📋 Details:")
        for key, value in error.details.items():
            lines.append(f"   - {key}: {value}")

    lines.append(f"\n📝 Error type: {error.__class__.__name__}")

    if include_traceback:
        import traceback
        lines.append("\n🔍 Stack trace:")
        lines.extend(traceback.format_tb(error.__traceback__))

    return "\n".join(lines)


def suggest_fix(error: Exception) -> Optional[str]:
    """
    Suggest potential fixes for common errors.

    Args:
        error: The exception to analyze

    Returns:
        Suggestion string or None if no suggestion available

    Example:
        >>> try:
        ...     raise ConfigurationError("Invalid spacing", {'spacing': -10})
        ... except SVIProError as e:
        ...     print(suggest_fix(e))
        "Consider using a positive spacing value (e.g., 50, 100, 200)"
    """
    if isinstance(error, ConfigurationError):
        if 'spacing' in str(error).lower():
            return "💡 Tip: Spacing must be a positive value in meters. Try values like 50, 100, or 200."
        if 'crs' in str(error).lower():
            return "💡 Tip: Use EPSG codes like 'EPSG:4326' (WGS84) or 'EPSG:3857' (Web Mercator)."
        if 'seed' in str(error).lower():
            return "💡 Tip: Seed must be a non-negative integer. Use None or 0 for random behavior."

    elif isinstance(error, BoundaryError):
        if 'area' in str(error).lower() or 'small' in str(error).lower():
            return "💡 Tip: Try a larger boundary or smaller spacing value."
        if 'invalid' in str(error).lower():
            return "💡 Tip: Check for self-intersections or use boundary.buffer(0) to fix geometry."

    elif isinstance(error, NetworkDownloadError):
        return "💡 Tip: Check your internet connection and try a smaller boundary or different network_type."

    elif isinstance(error, SamplingError):
        return "💡 Tip: Try reducing spacing or check if boundary has valid data."

    return None
