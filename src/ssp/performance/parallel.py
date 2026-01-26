"""
Parallel Processing Module

Provides parallel processing capabilities for large-scale sampling operations.
Uses multiprocessing to distribute work across multiple CPU cores.

Features:
- Automatic CPU core detection
- Chunk-based parallel processing
- Progress tracking
- Error handling and recovery
"""

import multiprocessing as mp
from typing import Callable, List, Any, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings


class ParallelProcessor:
    """
    Parallel processor for sampling operations.

    Distributes work across multiple CPU cores for faster processing
    of large sampling tasks.

    Example:
        >>> processor = ParallelProcessor(n_workers=4)
        >>> results = processor.map(
        ...     func=generate_samples,
        ...     items=list_of_boundaries,
        ...     config=sampling_config
        ... )
    """

    def __init__(self, n_workers: Optional[int] = None):
        """
        Initialize parallel processor.

        Args:
            n_workers: Number of worker processes. If None, uses CPU count.
        """
        if n_workers is None:
            n_workers = mp.cpu_count()

        self.n_workers = n_workers
        self._pool: Optional[ProcessPoolExecutor] = None

    def map(
        self,
        func: Callable,
        items: List[Any],
        **kwargs
    ) -> List[Any]:
        """
        Apply function to items in parallel.

        Args:
            func: Function to apply to each item.
            items: List of items to process.
            **kwargs: Additional keyword arguments passed to func.

        Returns:
            List of results in the same order as items.

        Raises:
            Exception: If any worker fails.
        """
        if not items:
            return []

        # Use single process for small lists
        if len(items) < self.n_workers:
            return [func(item, **kwargs) for item in items]

        results = [None] * len(items)

        with ProcessPoolExecutor(max_workers=self.n_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(func, item, **kwargs): idx
                for idx, item in enumerate(items)
            }

            # Collect results as they complete
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    raise Exception(
                        f"Worker failed on item {idx}: {e}"
                    )

        return results

    def map_chunks(
        self,
        func: Callable,
        items: List[Any],
        chunk_size: int,
        **kwargs
    ) -> List[Any]:
        """
        Apply function to chunks of items in parallel.

        Useful for processing many small items more efficiently
        by grouping them into chunks.

        Args:
            func: Function that takes a list of items.
            items: List of items to process.
            chunk_size: Number of items per chunk.
            **kwargs: Additional keyword arguments passed to func.

        Returns:
            List of results (flattened from chunks).

        Example:
            >>> def process_chunk(chunk):
            ...     return [x * 2 for x in chunk]
            >>> processor = ParallelProcessor()
            >>> results = processor.map_chunks(
            ...     func=process_chunk,
            ...     items=list(range(100)),
            ...     chunk_size=10
            ... )
        """
        if not items:
            return []

        # Split items into chunks
        chunks = [
            items[i:i + chunk_size]
            for i in range(0, len(items), chunk_size)
        ]

        # Process chunks in parallel
        chunk_results = self.map(func, chunks, **kwargs)

        # Flatten results
        results = []
        for chunk_result in chunk_results:
            if isinstance(chunk_result, list):
                results.extend(chunk_result)
            else:
                results.append(chunk_result)

        return results

    def starmap(
        self,
        func: Callable,
        args_list: List[Tuple[Any, ...]]
    ) -> List[Any]:
        """
        Apply function with multiple arguments in parallel.

        Like map, but for functions that take multiple arguments.

        Args:
            func: Function to apply.
            args_list: List of argument tuples.

        Returns:
            List of results.

        Example:
            >>> def add(a, b):
            ...     return a + b
            >>> processor = ParallelProcessor()
            >>> results = processor.starmap(
            ...     func=add,
            ...     args_list=[(1, 2), (3, 4), (5, 6)]
            ... )
            >>> # Results: [3, 7, 11]
        """
        if not args_list:
            return []

        def wrapper(args):
            return func(*args)

        return self.map(wrapper, args_list)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._pool is not None:
            self._pool.shutdown(wait=True)


def parallelize_sampling(
    strategy_func: Callable,
    boundaries: List[Any],
    n_workers: Optional[int] = None,
    **kwargs
) -> List[Any]:
    """
    Convenience function for parallel sampling.

    Args:
        strategy_func: Sampling strategy function (e.g., GridSampling().generate).
        boundaries: List of boundary polygons.
        n_workers: Number of worker processes.
        **kwargs: Additional arguments passed to strategy_func.

    Returns:
        List of GeoDataFrames with sample points.

    Example:
        >>> from shapely.geometry import box
        >>> from ssp import GridSampling, SamplingConfig
        >>> from ssp.performance import parallelize_sampling
        >>>
        >>> # Create multiple boundaries
        >>> boundaries = [box(i*1000, 0, (i+1)*1000, 1000) for i in range(10)]
        >>>
        >>> # Sample in parallel
        >>> results = parallelize_sampling(
        ...     strategy_func=GridSampling(SamplingConfig(spacing=100)).generate,
        ...     boundaries=boundaries,
        ...     n_workers=4
        ... )
    """
    processor = ParallelProcessor(n_workers=n_workers)
    return processor.map(strategy_func, boundaries, **kwargs)


def get_optimal_n_workers(task_type: str = "sampling") -> int:
    """
    Get optimal number of workers for a task type.

    Args:
        task_type: Type of task ('sampling', 'osm_download', 'general').

    Returns:
        Optimal number of workers.
    """
    cpu_count = mp.cpu_count()

    if task_type == "osm_download":
        # Limit network requests to avoid overloading servers
        return min(cpu_count, 4)
    elif task_type == "sampling":
        # Use most cores for CPU-intensive sampling
        return max(cpu_count - 1, 1)
    else:  # general
        return cpu_count
