"""
SpatialSamplingPro Performance Module

This module provides performance optimization tools for large-scale
sampling operations, including parallel processing, chunking,
caching, and progress tracking.

Main components:
- ParallelProcessor: Multi-core parallel processing
- SpatialChunker: Split large areas into manageable chunks
- DiskCache: Cache expensive operations to disk
- ProgressTracker: Track progress of long-running operations

Example usage:
    >>> from ssp.performance import (
    ...     ParallelProcessor,
    ...     SpatialChunker,
    ...     DiskCache,
    ...     ProgressTracker
    ... )
    >>>
    >>> # Parallel processing
    >>> processor = ParallelProcessor(n_workers=4)
    >>> results = processor.map(generate_samples, boundaries)
    >>>
    >>> # Spatial chunking
    >>> chunker = SpatialChunker(chunk_size_km=10)
    >>> for chunk in chunker.create_chunks(large_boundary):
    ...     points = strategy.generate(chunk)
    >>>
    >>> # Caching
    >>> cache = DiskCache(cache_dir="cache/")
    >>> result = cache.get("my_key")
    >>> if result is None:
    ...     result = expensive_operation()
    ...     cache.put("my_key", result)
"""

from ssp.performance.parallel import (
    ParallelProcessor,
    parallelize_sampling,
    get_optimal_n_workers
)

from ssp.performance.chunking import (
    SpatialChunker,
    TemporalChunker,
    StreamingGeoDataFrameProcessor,
    auto_chunk_size
)

from ssp.performance.cache import (
    DiskCache,
    Memoized,
    get_osm_cache,
    cached_osm_download,
    clear_all_caches
)

from ssp.performance.progress import (
    ProgressTracker,
    progress_context,
    track_progress,
    track_parallel_progress,
    SamplingProgressTracker,
    require_tqdm,
    TQDM_AVAILABLE
)

__all__ = [
    # Parallel processing
    'ParallelProcessor',
    'parallelize_sampling',
    'get_optimal_n_workers',

    # Chunking
    'SpatialChunker',
    'TemporalChunker',
    'StreamingGeoDataFrameProcessor',
    'auto_chunk_size',

    # Caching
    'DiskCache',
    'Memoized',
    'get_osm_cache',
    'cached_osm_download',
    'clear_all_caches',

    # Progress tracking
    'ProgressTracker',
    'progress_context',
    'track_progress',
    'track_parallel_progress',
    'SamplingProgressTracker',
    'require_tqdm',
    'TQDM_AVAILABLE',
]
