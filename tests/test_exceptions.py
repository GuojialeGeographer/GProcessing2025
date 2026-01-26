"""
Unit tests for exception handling module.

Tests SpatialSamplingPro custom exceptions and error handling utilities.
"""

import pytest
from ssp.exceptions import (
    SpatialSamplingProError,
    ConfigurationError,
    BoundaryError,
    SamplingError,
    NetworkDownloadError,
    ValidationError,
    ExportError,
    VisualizationError,
    format_error_context,
    suggest_fix
)


class TestSpatialSamplingProError:
    """Test suite for base SpatialSamplingProError class."""

    def test_basic_error_initialization(self):
        """Test basic error initialization."""
        error = SpatialSamplingProError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.details == {}

    def test_error_with_details(self):
        """Test error initialization with details dictionary."""
        details = {'spacing': -10, 'valid_range': '(0, inf)'}
        error = ConfigurationError("Invalid spacing", details=details)

        assert error.details == details
        assert 'spacing' in error.details

    def test_error_to_dict(self):
        """Test error serialization to dictionary."""
        details = {'param': 'value', 'number': 42}
        error = ValidationError("Validation failed", details=details)

        error_dict = error.to_dict()
        assert error_dict['error_type'] == 'ValidationError'
        assert error_dict['message'] == 'Validation failed'
        assert error_dict['details'] == details

    def test_all_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from SpatialSamplingProError."""
        exceptions = [
            ConfigurationError,
            BoundaryError,
            SamplingError,
            NetworkDownloadError,
            ValidationError,
            ExportError,
            VisualizationError
        ]

        for exc_class in exceptions:
            error = exc_class("test message")
            assert isinstance(error, SpatialSamplingProError)
            assert isinstance(error, Exception)


class TestConfigurationError:
    """Test suite for ConfigurationError."""

    def test_configuration_error_message(self):
        """Test configuration error message."""
        error = ConfigurationError("Invalid CRS value")
        assert "Invalid CRS value" in str(error)

    def test_configuration_error_with_spacing_details(self):
        """Test configuration error with spacing details."""
        error = ConfigurationError(
            "Invalid spacing",
            details={'spacing': -100, 'expected': 'positive value'}
        )

        assert error.details['spacing'] == -100
        assert error.details['expected'] == 'positive value'


class TestBoundaryError:
    """Test suite for BoundaryError."""

    def test_boundary_error_message(self):
        """Test boundary error message."""
        error = BoundaryError("Boundary too small")
        assert "Boundary too small" in str(error)

    def test_boundary_error_with_area_details(self):
        """Test boundary error with area details."""
        error = BoundaryError(
            "Boundary area insufficient",
            details={'area_km2': 0.001, 'min_area_km2': 1.0}
        )

        assert error.details['area_km2'] == 0.001
        assert error.details['min_area_km2'] == 1.0


class TestNetworkDownloadError:
    """Test suite for NetworkDownloadError."""

    def test_network_error_message(self):
        """Test network download error message."""
        error = NetworkDownloadError("OSM server timeout")
        assert "OSM server timeout" in str(error)

    def test_network_error_with_network_type(self):
        """Test network error with network type details."""
        error = NetworkDownloadError(
            "Failed to download road network",
            details={'network_type': 'drive', 'timeout': 30}
        )

        assert error.details['network_type'] == 'drive'
        assert error.details['timeout'] == 30


class TestFormatErrorContext:
    """Test suite for format_error_context utility."""

    def test_format_simple_error(self):
        """Test formatting a simple error."""
        error = ValueError("Simple error")
        formatted = format_error_context(error, include_traceback=False)

        assert "❌ Error: Simple error" in formatted
        assert "ValueError" in formatted

    def test_format_spatial_sampling_pro_error_without_details(self):
        """Test formatting SpatialSamplingPro error without details."""
        error = ConfigurationError("Invalid configuration")
        formatted = format_error_context(error, include_traceback=False)

        assert "❌ Error: Invalid configuration" in formatted
        assert "ConfigurationError" in formatted

    def test_format_spatial_sampling_pro_error_with_details(self):
        """Test formatting SpatialSamplingPro error with details."""
        details = {'spacing': -10, 'min': 1}
        error = ConfigurationError("Invalid spacing", details=details)
        formatted = format_error_context(error, include_traceback=False)

        assert "❌ Error: Invalid spacing" in formatted
        assert "📋 Details:" in formatted
        assert "- spacing: -10" in formatted
        assert "- min: 1" in formatted

    def test_format_with_traceback(self):
        """Test formatting error with traceback."""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            formatted = format_error_context(e, include_traceback=True)
            assert "🔍 Stack trace:" in formatted


class TestSuggestFix:
    """Test suite for suggest_fix utility."""

    def test_suggest_fix_for_configuration_spacing(self):
        """Test fix suggestion for spacing configuration error."""
        error = ConfigurationError("Invalid spacing value", {'spacing': -10})
        suggestion = suggest_fix(error)

        assert suggestion is not None
        assert "💡 Tip:" in suggestion
        assert "spacing" in suggestion.lower()
        assert "positive" in suggestion.lower()

    def test_suggest_fix_for_configuration_crs(self):
        """Test fix suggestion for CRS configuration error."""
        error = ConfigurationError("Invalid CRS", {'crs': 'INVALID'})
        suggestion = suggest_fix(error)

        assert suggestion is not None
        assert "EPSG" in suggestion
        assert "4326" in suggestion or "3857" in suggestion

    def test_suggest_fix_for_boundary_area(self):
        """Test fix suggestion for boundary area error."""
        error = BoundaryError("Boundary too small", {'area': 0.001})
        suggestion = suggest_fix(error)

        assert suggestion is not None
        assert "larger boundary" in suggestion.lower() or "smaller spacing" in suggestion.lower()

    def test_suggest_fix_for_network_download(self):
        """Test fix suggestion for network download error."""
        error = NetworkDownloadError("OSM download failed")
        suggestion = suggest_fix(error)

        assert suggestion is not None
        assert "internet" in suggestion.lower()

    def test_suggest_fix_for_unknown_error(self):
        """Test that unknown errors return no suggestion."""
        error = ValueError("Unknown error type")
        suggestion = suggest_fix(error)

        # Non-SpatialSamplingPro errors have no specific suggestions
        assert suggestion is None or "Tip:" in suggestion

    def test_suggest_fix_for_sampling_error(self):
        """Test fix suggestion for sampling error."""
        error = SamplingError("No points generated")
        suggestion = suggest_fix(error)

        assert suggestion is not None
        assert "spacing" in suggestion.lower()

    def test_suggest_fix_for_validation_error(self):
        """Test that validation errors get generic handling."""
        error = ValidationError("Invalid file format")
        suggestion = suggest_fix(error)

        # May be None or generic
        assert suggestion is None or isinstance(suggestion, str)


class TestExceptionChaining:
    """Test suite for exception chaining patterns."""

    def test_raise_configuration_error_from_validation(self):
        """Test raising ConfigurationError from validation failure."""
        with pytest.raises(ConfigurationError) as exc_info:
            if -10 <= 0:
                raise ConfigurationError(
                    "Spacing must be positive",
                    details={'provided_value': -10}
                )

        assert "Spacing must be positive" in str(exc_info.value)
        assert exc_info.value.details['provided_value'] == -10

    def test_exception_as_context_manager(self):
        """Test using exceptions in context managers."""
        error = BoundaryError("Invalid boundary", {'area': 0})

        with pytest.raises(BoundaryError) as exc_info:
            raise error

        assert exc_info.value is error

    def test_catching_base_exception_class(self):
        """Test catching all SpatialSamplingPro errors with base class."""
        errors = [
            ConfigurationError("config"),
            BoundaryError("boundary"),
            SamplingError("sampling"),
        ]

        for error in errors:
            with pytest.raises(SpatialSamplingProError):
                raise error


class TestErrorDetailsValidation:
    """Test suite for error details validation."""

    def test_error_details_accept_common_types(self):
        """Test that error details accept common data types."""
        details = {
            'string': 'value',
            'integer': 42,
            'float': 3.14,
            'list': [1, 2, 3],
            'dict': {'nested': 'value'},
            'none': None,
            'bool': True
        }

        error = ValidationError("Test", details=details)

        for key, value in details.items():
            assert error.details[key] == value

    def test_error_details_empty_dict(self):
        """Test that empty details dictionary is handled."""
        error = ExportError("Export failed", details={})
        assert error.details == {}

    def test_error_details_none_becomes_empty_dict(self):
        """Test that None details becomes empty dictionary."""
        error = VisualizationError("Render failed", details=None)
        assert error.details == {}
