"""
Progress Module

Provides progress tracking for long-running operations.

Features:
- Progress bars for sampling operations
- Progress tracking for parallel processing
- ETA calculation
- Flexible output (terminal, notebook, silent)
"""

import time
import sys
from typing import Optional, Callable, Any, List
from contextlib import contextmanager

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class ProgressTracker:
    """
    Progress tracker for operations.

    Example:
        >>> tracker = ProgressTracker(total=100, description="Processing")
        >>> for i in range(100):
        ...     # Do work
        ...     tracker.update(1)
        >>> tracker.close()
    """

    def __init__(
        self,
        total: int,
        description: str = "Processing",
        show_progress: bool = True,
        silent: bool = False
    ):
        """
        Initialize progress tracker.

        Args:
            total: Total number of items to process.
            description: Description of the operation.
            show_progress: If False, disables progress bar.
            silent: If True, completely silent mode.
        """
        self.total = total
        self.description = description
        self.show_progress = show_progress and TQDM_AVAILABLE and not silent
        self.silent = silent

        self._pbar = None
        self._start_time = None
        self._completed = 0

        if self.show_progress:
            self._pbar = tqdm(
                total=total,
                desc=description,
                unit='item',
                disable=False
            )
            self._start_time = time.time()

    def update(self, n: int = 1) -> None:
        """
        Update progress.

        Args:
            n: Number of items completed.
        """
        self._completed += n

        if self._pbar:
            self._pbar.update(n)
        elif not self.silent:
            # Simple text progress
            percent = (self._completed / self.total) * 100
            print(f"\r{self.description}: {self._completed}/{self.total} ({percent:.1f}%)", end='')
            sys.stdout.flush()

    def close(self) -> None:
        """Close progress tracker."""
        if self._pbar:
            self._pbar.close()
        elif not self.silent and self._completed > 0:
            print()  # New line after text progress

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def get_elapsed_time(self) -> float:
        """
        Get elapsed time in seconds.

        Returns:
            Elapsed time since start.
        """
        if self._start_time:
            return time.time() - self._start_time
        return 0.0

    def get_eta(self) -> float:
        """
        Get estimated time to completion.

        Returns:
            ETA in seconds.
        """
        if self._completed == 0:
            return 0.0

        elapsed = self.get_elapsed_time()
        if elapsed == 0:
            return 0.0

        rate = self._completed / elapsed
        remaining = self.total - self._completed

        return remaining / rate


@contextmanager
def progress_context(
    total: int,
    description: str = "Processing",
    show_progress: bool = True
):
    """
    Context manager for progress tracking.

    Args:
        total: Total number of items.
        description: Operation description.
        show_progress: Whether to show progress.

    Yields:
        ProgressTracker instance.

    Example:
        >>> with progress_context(100, "Sampling") as tracker:
        ...     for i in range(100):
        ...         # Do work
        ...         tracker.update(1)
    """
    tracker = ProgressTracker(total, description, show_progress)
    try:
        yield tracker
    finally:
        tracker.close()


def track_progress(
    func: Callable,
    items: List[Any],
    description: str = "Processing",
    show_progress: bool = True
) -> List[Any]:
    """
    Apply function to items with progress tracking.

    Args:
        func: Function to apply to each item.
        items: List of items to process.
        description: Operation description.
        show_progress: Whether to show progress.

    Returns:
        List of results.

    Example:
        >>> def process_item(item):
        ...     return item * 2
        >>>
        >>> results = track_progress(
        ...     func=process_item,
        ...     items=list(range(100)),
        ...     description="Doubling numbers"
        ... )
    """
    results = []

    with progress_context(len(items), description, show_progress) as tracker:
        for item in items:
            result = func(item)
            results.append(result)
            tracker.update(1)

    return results


def track_parallel_progress(
    func: Callable,
    items: List[Any],
    n_workers: int = 4,
    description: str = "Parallel processing",
    show_progress: bool = True
) -> List[Any]:
    """
    Apply function to items in parallel with progress tracking.

    Args:
        func: Function to apply to each item.
        items: List of items to process.
        n_workers: Number of worker processes.
        description: Operation description.
        show_progress: Whether to show progress.

    Returns:
        List of results.

    Example:
        >>> from ssp.performance import track_parallel_progress
        >>>
        >>> def expensive_computation(x):
        ...     return x ** 2
        >>>
        >>> results = track_parallel_progress(
        ...     func=expensive_computation,
        ...     items=list(range(1000)),
        ...     n_workers=4,
        ...     description="Computing squares"
        ... )
    """
    from concurrent.futures import ProcessPoolExecutor, as_completed

    results = [None] * len(items)

    with progress_context(len(items), description, show_progress) as tracker:
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(func, item): idx
                for idx, item in enumerate(items)
            }

            # Collect results as they complete
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    results[idx] = e

                tracker.update(1)

    return results


class SamplingProgressTracker:
    """
    Specialized progress tracker for sampling operations.

    Tracks different stages of sampling:
    - Initialization
    - Point generation
    - Validation
    - Export

    Example:
        >>> tracker = SamplingProgressTracker()
        >>> tracker.start_initialization(10)
        >>> # Initialize 10 chunks
        >>> tracker.complete_initialization()
        >>>
        >>> tracker.start_sampling(1000)
        >>> # Generate 1000 points
        >>> tracker.update_sampling(100)
        >>> tracker.complete_sampling()
    """

    def __init__(self, show_progress: bool = True):
        """
        Initialize sampling progress tracker.

        Args:
            show_progress: Whether to show progress bars.
        """
        self.show_progress = show_progress
        self._stages = {}

    def start_initialization(self, n_chunks: int) -> None:
        """Start initialization stage."""
        self._stages['initialization'] = ProgressTracker(
            total=n_chunks,
            description="Initializing",
            show_progress=self.show_progress
        )

    def update_initialization(self, n: int = 1) -> None:
        """Update initialization progress."""
        if 'initialization' in self._stages:
            self._stages['initialization'].update(n)

    def complete_initialization(self) -> None:
        """Complete initialization stage."""
        if 'initialization' in self._stages:
            self._stages['initialization'].close()

    def start_sampling(self, n_points: int) -> None:
        """Start sampling stage."""
        self._stages['sampling'] = ProgressTracker(
            total=n_points,
            description="Sampling points",
            show_progress=self.show_progress
        )

    def update_sampling(self, n: int = 1) -> None:
        """Update sampling progress."""
        if 'sampling' in self._stages:
            self._stages['sampling'].update(n)

    def complete_sampling(self) -> None:
        """Complete sampling stage."""
        if 'sampling' in self._stages:
            self._stages['sampling'].close()

    def start_validation(self, n_items: int) -> None:
        """Start validation stage."""
        self._stages['validation'] = ProgressTracker(
            total=n_items,
            description="Validating",
            show_progress=self.show_progress
        )

    def update_validation(self, n: int = 1) -> None:
        """Update validation progress."""
        if 'validation' in self._stages:
            self._stages['validation'].update(n)

    def complete_validation(self) -> None:
        """Complete validation stage."""
        if 'validation' in self._stages:
            self._stages['validation'].close()

    def start_export(self, n_items: int) -> None:
        """Start export stage."""
        self._stages['export'] = ProgressTracker(
            total=n_items,
            description="Exporting",
            show_progress=self.show_progress
        )

    def update_export(self, n: int = 1) -> None:
        """Update export progress."""
        if 'export' in self._stages:
            self._stages['export'].update(n)

    def complete_export(self) -> None:
        """Complete export stage."""
        if 'export' in self._stages:
            self._stages['export'].close()

    def complete_all(self) -> None:
        """Complete all stages."""
        for stage in self._stages.values():
            stage.close()


def require_tqdm(func: Callable) -> Callable:
    """
    Decorator to require tqdm for progress tracking.

    Args:
        func: Function to decorate.

    Returns:
        Decorated function.

    Example:
        >>> @require_tqdm
        >>> def operation_with_progress():
        ...     tracker = ProgressTracker(100)
        ...     for i in range(100):
        ...         tracker.update(1)
        ...     tracker.close()
    """
    def wrapper(*args, **kwargs):
        if not TQDM_AVAILABLE:
            raise ImportError(
                f"{func.__name__} requires tqdm. "
                "Install it with: pip install tqdm"
            )
        return func(*args, **kwargs)
    return wrapper
