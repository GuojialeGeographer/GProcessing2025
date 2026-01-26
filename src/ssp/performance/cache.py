"""
Cache Module

Provides caching mechanisms to avoid redundant expensive operations
like OSM downloads and repetitive sampling.

Features:
- Disk-based caching for OSM networks
- In-memory caching for sampling results
- Cache invalidation and management
- Thread-safe operations
"""

import hashlib
import pickle
import json
from typing import Optional, Any, Dict, Callable
from pathlib import Path
from datetime import datetime, timedelta
import functools
from threading import Lock


class DiskCache:
    """
    Disk-based cache for expensive computations.

    Useful for caching:
    - OSM road network downloads
    - Large sampling computations
    - Expensive metric calculations

    Example:
        >>> cache = DiskCache(cache_dir="cache/")
        >>>
        >>> # Check cache before expensive operation
        >>> result = cache.get("my_key")
        >>> if result is None:
        ...     result = expensive_computation()
        ...     cache.put("my_key", result)
    """

    def __init__(
        self,
        cache_dir: str = ".ssp_cache",
        max_age_days: int = 7,
        max_size_mb: int = 1024
    ):
        """
        Initialize disk cache.

        Args:
            cache_dir: Directory to store cache files.
            max_age_days: Maximum age of cache files in days.
            max_size_mb: Maximum cache size in MB.
        """
        self.cache_dir = Path(cache_dir)
        self.max_age_days = max_age_days
        self.max_size_mb = max_size_mb
        self.lock = Lock()

        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Create metadata file
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_metadata(self) -> None:
        """Save cache metadata to disk."""
        with self.lock:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)

    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Hash key to create safe filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.pkl"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value, or None if not found or expired.

        Example:
            >>> result = cache.get("my_key")
            >>> if result is not None:
            ...     print("Cache hit!")
        """
        cache_path = self._get_cache_path(key)

        with self.lock:
            # Check if file exists
            if not cache_path.exists():
                return None

            # Check if expired
            if key in self.metadata:
                cached_time = datetime.fromisoformat(
                    self.metadata[key]['timestamp']
                )
                age = datetime.now() - cached_time

                if age > timedelta(days=self.max_age_days):
                    # Expired, delete file
                    cache_path.unlink()
                    del self.metadata[key]
                    self._save_metadata()
                    return None

            # Load from disk
            try:
                with open(cache_path, 'rb') as f:
                    value = pickle.load(f)

                # Update access time
                if key in self.metadata:
                    self.metadata[key]['last_access'] = datetime.now().isoformat()
                    self._save_metadata()

                return value
            except Exception:
                # Cache corruption, delete file
                cache_path.unlink()
                return None

    def put(self, key: str, value: Any) -> None:
        """
        Put value into cache.

        Args:
            key: Cache key.
            value: Value to cache.

        Example:
            >>> cache.put("my_key", expensive_result)
        """
        cache_path = self._get_cache_path(key)

        with self.lock:
            # Save to disk
            try:
                with open(cache_path, 'wb') as f:
                    pickle.dump(value, f)

                # Update metadata
                self.metadata[key] = {
                    'timestamp': datetime.now().isoformat(),
                    'last_access': datetime.now().isoformat(),
                    'size_bytes': cache_path.stat().st_size
                }

                self._save_metadata()

                # Clean up if cache is too large
                self._cleanup_if_needed()

            except Exception as e:
                # Failed to cache, continue without caching
                warnings.warn(f"Failed to cache key '{key}': {e}")

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key.

        Returns:
            True if deleted, False if not found.

        Example:
            >>> cache.delete("my_key")
        """
        cache_path = self._get_cache_path(key)

        with self.lock:
            if cache_path.exists():
                cache_path.unlink()

            if key in self.metadata:
                del self.metadata[key]
                self._save_metadata()
                return True

            return False

    def clear(self) -> None:
        """
        Clear all cache entries.

        Example:
            >>> cache.clear()
        """
        with self.lock:
            # Delete all cache files
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()

            # Clear metadata
            self.metadata.clear()
            self._save_metadata()

    def _cleanup_if_needed(self) -> None:
        """Clean up old cache entries if cache is too large."""
        # Calculate total cache size
        total_size = sum(
            meta['size_bytes']
            for meta in self.metadata.values()
        )

        max_size_bytes = self.max_size_mb * 1024 * 1024

        if total_size > max_size_bytes:
            # Sort by last access time
            sorted_keys = sorted(
                self.metadata.keys(),
                key=lambda k: self.metadata[k]['last_access']
            )

            # Delete oldest entries until under limit
            for key in sorted_keys:
                self.delete(key)

                total_size = sum(
                    meta['size_bytes']
                    for meta in self.metadata.values()
                )

                if total_size <= max_size_bytes:
                    break

    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            Number of entries removed.

        Example:
            >>> n_removed = cache.cleanup_expired()
            >>> print(f"Removed {n_removed} expired entries")
        """
        with self.lock:
            removed = 0
            now = datetime.now()

            for key in list(self.metadata.keys()):
                cached_time = datetime.fromisoformat(
                    self.metadata[key]['timestamp']
                )
                age = now - cached_time

                if age > timedelta(days=self.max_age_days):
                    self.delete(key)
                    removed += 1

            return removed

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics.

        Example:
            >>> stats = cache.get_stats()
            >>> print(f"Cache entries: {stats['n_entries']}")
            >>> print(f"Cache size: {stats['size_mb']} MB")
        """
        total_size = sum(
            meta['size_bytes']
            for meta in self.metadata.values()
        )

        return {
            'n_entries': len(self.metadata),
            'size_mb': round(total_size / (1024 * 1024), 2),
            'max_size_mb': self.max_size_mb,
            'max_age_days': self.max_age_days,
            'cache_dir': str(self.cache_dir)
        }


class Memoized:
    """
    Memoization decorator for functions.

    Caches function results in memory.

    Example:
        >>> @Memoized
        >>> def expensive_function(x, y):
        ...     # Expensive computation
        ...     return x + y
        >>>
        >>> # First call computes result
        >>> result1 = expensive_function(1, 2)
        >>> # Second call uses cache
        >>> result2 = expensive_function(1, 2)
    """

    def __init__(self, func: Callable):
        """
        Initialize memoization.

        Args:
            func: Function to memoize.
        """
        self.func = func
        self.cache = {}
        self.lock = Lock()

    def __call__(self, *args, **kwargs):
        """Call function with caching."""
        # Create cache key from arguments
        key = self._make_key(args, kwargs)

        with self.lock:
            if key not in self.cache:
                self.cache[key] = self.func(*args, **kwargs)

            return self.cache[key]

    def _make_key(self, args, kwargs) -> tuple:
        """Create cache key from arguments."""
        # For simplicity, convert to string
        # In production, you'd want a more sophisticated approach
        args_str = str(args)
        kwargs_str = str(sorted(kwargs.items()))
        return (args_str, kwargs_str)

    def cache_clear(self):
        """Clear cache."""
        with self.lock:
            self.cache.clear()

    def cache_info(self) -> Dict[str, int]:
        """Get cache information."""
        return {
            'size': len(self.cache)
        }


# Global cache instance for OSM networks
_osm_cache: Optional[DiskCache] = None


def get_osm_cache() -> DiskCache:
    """
    Get global OSM cache instance.

    Returns:
        DiskCache instance for OSM data.

    Example:
        >>> cache = get_osm_cache()
        >>> graph = cache.get("osm_graph_123")
        >>> if graph is None:
        ...     graph = download_osm_graph()
        ...     cache.put("osm_graph_123", graph)
    """
    global _osm_cache

    if _osm_cache is None:
        _osm_cache = DiskCache(
            cache_dir=".ssp_cache/osm",
            max_age_days=30,  # OSM data valid for 30 days
            max_size_mb=512   # Max 512MB for OSM cache
        )

    return _osm_cache


def cached_osm_download(
    download_func: Callable,
    cache_key: str,
    *args,
    **kwargs
) -> Any:
    """
    Wrapper for OSM downloads with caching.

    Args:
        download_func: Function to download OSM data.
        cache_key: Unique key for this download.
        *args: Arguments passed to download_func.
        **kwargs: Keyword arguments passed to download_func.

    Returns:
        Downloaded OSM data (from cache if available).

    Example:
        >>> def download_hk_network():
        ...     import osmnx as ox
        ...     return ox.graph_from_polygon(boundary)
        >>>
        >>> graph = cached_osm_download(
        ...     download_func=download_hk_network,
        ...     cache_key="hk_network_v1"
        ... )
    """
    cache = get_osm_cache()

    # Check cache
    result = cache.get(cache_key)
    if result is not None:
        return result

    # Download
    result = download_func(*args, **kwargs)

    # Cache result
    cache.put(cache_key, result)

    return result


def clear_all_caches() -> None:
    """
    Clear all SpatialSamplingPro caches.

    Example:
        >>> clear_all_caches()
        >>> print("All caches cleared")
    """
    # Clear OSM cache
    osm_cache = get_osm_cache()
    osm_cache.clear()

    # Clear other caches if they exist
    cache_dir = Path(".ssp_cache")
    if cache_dir.exists():
        for subcache_dir in cache_dir.iterdir():
            if subcache_dir.is_dir():
                cache = DiskCache(cache_dir=str(subcache_dir))
                cache.clear()
