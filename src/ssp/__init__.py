"""
SpatialSamplingPro: Spatial Sampling Design & Protocol Optimization

A standardized framework for reproducible spatial sampling design.
This package provides scientific sampling strategies, metadata management, and
reproducibility tools for geospatial studies and research.

Core Modules:
    - sampling: Scientific spatial sampling strategies
    - metadata: Standardized metadata generation and management
    - visualization: Tools for sampling evaluation and visualization
    - performance: Optimization and parallel processing tools
    - utils: Utility functions and helpers
    - cli: Command-line interface

Authors:
    Jiale Guo (jiale.guo@mail.polimi.it)
    Mingfeng Tang (mingfeng.tang@mail.polimi.it)

Geoinformatics Engineering graduate students at Politecnico di Milano
"""

__version__ = "0.1.0"
__author__ = "Jiale Guo, Mingfeng Tang"

from ssp.sampling.base import SamplingConfig
from ssp.sampling import SamplingStrategy, GridSampling, RoadNetworkSampling
from ssp.visualization import compare_strategies, plot_coverage_statistics, plot_spatial_distribution
from ssp.metadata import (
    SamplingMetadata,
    MetadataSerializer,
    MetadataValidator,
    MetadataExporter,
    quick_validate
)
from ssp.performance import (
    ParallelProcessor,
    SpatialChunker,
    DiskCache,
    ProgressTracker,
    TQDM_AVAILABLE
)
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
from ssp.utils import (
    handle_small_boundary,
    fix_invalid_geometry,
    ensure_polygon,
    validate_crs_compatibility,
    handle_empty_geodataframe,
    warn_large_output,
    estimate_processing_time,
    check_spacing_bounds,
    safe_geometry_operation,
    meters_to_degrees,
    degrees_to_meters,
    estimate_center_latitude,
    convert_spacing_for_crs
)

__all__ = [
    "__version__",
    "__author__",
    # Sampling
    "SamplingConfig",
    "SamplingStrategy",
    "GridSampling",
    "RoadNetworkSampling",
    # Visualization
    "compare_strategies",
    "plot_coverage_statistics",
    "plot_spatial_distribution",
    # Metadata
    "SamplingMetadata",
    "MetadataSerializer",
    "MetadataValidator",
    "MetadataExporter",
    "quick_validate",
    # Performance
    "ParallelProcessor",
    "SpatialChunker",
    "DiskCache",
    "ProgressTracker",
    "TQDM_AVAILABLE",
    # Exceptions
    "SpatialSamplingProError",
    "ConfigurationError",
    "BoundaryError",
    "SamplingError",
    "NetworkDownloadError",
    "ValidationError",
    "ExportError",
    "VisualizationError",
    "format_error_context",
    "suggest_fix",
    # Utils
    "handle_small_boundary",
    "fix_invalid_geometry",
    "ensure_polygon",
    "validate_crs_compatibility",
    "handle_empty_geodataframe",
    "warn_large_output",
    "estimate_processing_time",
    "check_spacing_bounds",
    "safe_geometry_operation",
    "meters_to_degrees",
    "degrees_to_meters",
    "estimate_center_latitude",
    "convert_spacing_for_crs",
]
