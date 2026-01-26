"""
Chunking Module

Provides spatial and temporal chunking capabilities for processing
large datasets that don't fit in memory.

Features:
- Spatial chunking (grid-based)
- Temporal chunking (batch processing)
- Memory-efficient streaming
- Automatic chunk size optimization
"""

from typing import List, Tuple, Optional, Callable, Any, Iterator
import numpy as np
from shapely.geometry import Polygon, box
import geopandas as gpd
from pathlib import Path


class SpatialChunker:
    """
    Splits large areas into smaller chunks for processing.

    Useful for:
    - Processing large study areas that exceed memory limits
    - Parallel processing of sub-regions
    - Handling network timeouts for OSM downloads

    Example:
        >>> from shapely.geometry import box
        >>> chunker = SpatialChunker(chunk_size_km=10)
        >>> boundary = box(0, 0, 50000, 50000)  # 50km x 50km
        >>> chunks = list(chunker.create_chunks(boundary))
        >>> print(f"Created {len(chunks)} chunks")
    """

    def __init__(
        self,
        chunk_size_km: float = 10.0,
        overlap_m: float = 0.0,
        crs: str = "EPSG:4326"
    ):
        """
        Initialize spatial chunker.

        Args:
            chunk_size_km: Size of each chunk in kilometers.
            overlap_m: Overlap between chunks in meters (to avoid edge effects).
            crs: Coordinate reference system.
        """
        self.chunk_size_km = chunk_size_km
        self.overlap_m = overlap_m
        self.crs = crs

        # Convert chunk size to meters (approximate)
        self.chunk_size_m = chunk_size_km * 1000

    def create_chunks(
        self,
        boundary: Polygon,
        max_chunks: Optional[int] = None
    ) -> Iterator[Polygon]:
        """
        Create chunks from boundary.

        Args:
            boundary: Boundary polygon to chunk.
            max_chunks: Maximum number of chunks to create (for testing).

        Yields:
            Polygon chunks.

        Example:
            >>> chunker = SpatialChunker(chunk_size_km=5)
            >>> boundary = box(0, 0, 20000, 20000)
            >>> for i, chunk in enumerate(chunker.create_chunks(boundary)):
            ...     print(f"Chunk {i}: {chunk.area} m²")
        """
        # Get boundary bounds
        minx, miny, maxx, maxy = boundary.bounds

        # Calculate number of chunks in each dimension
        width = maxx - minx
        height = maxy - miny

        n_chunks_x = int(np.ceil(width / self.chunk_size_m))
        n_chunks_y = int(np.ceil(height / self.chunk_size_m))

        chunk_count = 0

        for i in range(n_chunks_x):
            for j in range(n_chunks_y):
                # Calculate chunk bounds with overlap
                chunk_minx = minx + i * self.chunk_size_m - self.overlap_m
                chunk_miny = miny + j * self.chunk_size_m - self.overlap_m
                chunk_maxx = min(
                    minx + (i + 1) * self.chunk_size_m + self.overlap_m,
                    maxx
                )
                chunk_maxy = min(
                    miny + (j + 1) * self.chunk_size_m + self.overlap_m,
                    maxy
                )

                # Create chunk polygon
                chunk = box(chunk_minx, chunk_miny, chunk_maxx, chunk_maxy)

                # Intersect with boundary
                chunk = chunk.intersection(boundary)

                # Skip empty chunks
                if chunk.is_empty or chunk.area == 0:
                    continue

                yield chunk

                chunk_count += 1

                # Stop if max chunks reached
                if max_chunks and chunk_count >= max_chunks:
                    return

    def estimate_chunk_count(self, boundary: Polygon) -> int:
        """
        Estimate number of chunks for a boundary.

        Args:
            boundary: Boundary polygon.

        Returns:
            Estimated number of chunks.
        """
        minx, miny, maxx, maxy = boundary.bounds
        width = maxx - minx
        height = maxy - miny

        n_chunks_x = int(np.ceil(width / self.chunk_size_m))
        n_chunks_y = int(np.ceil(height / self.chunk_size_m))

        return n_chunks_x * n_chunks_y

    def optimize_chunk_size(
        self,
        boundary: Polygon,
        target_chunk_count: int = 100
    ) -> float:
        """
        Optimize chunk size for target number of chunks.

        Args:
            boundary: Boundary polygon.
            target_chunk_count: Desired number of chunks.

        Returns:
            Optimal chunk size in kilometers.
        """
        minx, miny, maxx, maxy = boundary.bounds
        width = maxx - minx
        height = maxy - miny

        # Area in square kilometers
        area_m2 = width * height
        area_km2 = area_m2 / 1e6

        # Chunk size to achieve target count
        chunk_area_km2 = area_km2 / target_chunk_count
        chunk_size_km = np.sqrt(chunk_area_km2)

        return chunk_size_km


class TemporalChunker:
    """
    Splits large datasets into temporal batches for streaming processing.

    Example:
        >>> chunker = TemporalChunker(chunk_size=1000)
        >>> for chunk in chunker.process_items(large_list):
        ...     # Process chunk of 1000 items
        ...     process(chunk)
    """

    def __init__(self, chunk_size: int = 1000):
        """
        Initialize temporal chunker.

        Args:
            chunk_size: Number of items per chunk.
        """
        self.chunk_size = chunk_size

    def chunk_list(self, items: List[Any]) -> Iterator[List[Any]]:
        """
        Split list into chunks.

        Args:
            items: List of items to chunk.

        Yields:
            Chunks of items.

        Example:
            >>> chunker = TemporalChunker(chunk_size=3)
            >>> items = list(range(10))
            >>> chunks = list(chunker.chunk_list(items))
            >>> # chunks: [[0,1,2], [3,4,5], [6,7,8], [9]]
        """
        for i in range(0, len(items), self.chunk_size):
            yield items[i:i + self.chunk_size]

    def chunk_generator(
        self,
        generator: Iterator[Any]
    ) -> Iterator[List[Any]]:
        """
        Chunk items from a generator.

        Useful for processing large files or streams.

        Args:
            generator: Generator yielding items.

        Yields:
            Chunks of items.

        Example:
            >>> def read_large_file():
            ...     with open('large.txt') as f:
            ...         for line in f:
            ...             yield line
            >>> chunker = TemporalChunker(chunk_size=1000)
            >>> for chunk in chunker.chunk_generator(read_large_file()):
            ...     process(chunk)
        """
        chunk = []
        for item in generator:
            chunk.append(item)
            if len(chunk) >= self.chunk_size:
                yield chunk
                chunk = []

        # Yield remaining items
        if chunk:
            yield chunk

    def estimate_chunk_count(self, n_items: int) -> int:
        """
        Estimate number of chunks for item count.

        Args:
            n_items: Total number of items.

        Returns:
            Estimated number of chunks.
        """
        return int(np.ceil(n_items / self.chunk_size))


class StreamingGeoDataFrameProcessor:
    """
    Process large GeoDataFrames in chunks to avoid memory issues.

    Example:
        >>> processor = StreamingGeoDataFrameProcessor(chunk_size=1000)
        >>> results = processor.process_large_gdf(
        ...     large_gdf,
        ...     process_func=lambda chunk: chunk.buffer(10)
        ... )
    """

    def __init__(self, chunk_size: int = 1000):
        """
        Initialize streaming processor.

        Args:
            chunk_size: Number of features per chunk.
        """
        self.chunk_size = chunk_size

    def process_large_gdf(
        self,
        gdf: gpd.GeoDataFrame,
        process_func: Callable[[gpd.GeoDataFrame], gpd.GeoDataFrame],
        show_progress: bool = False
    ) -> gpd.GeoDataFrame:
        """
        Process large GeoDataFrame in chunks.

        Args:
            gdf: Large GeoDataFrame to process.
            process_func: Function to apply to each chunk.
            show_progress: If True, shows progress.

        Returns:
            Processed GeoDataFrame.

        Example:
            >>> def densify_points(chunk):
            ...     # Add some processing logic
            ...     return chunk
            >>> processor = StreamingGeoDataFrameProcessor()
            >>> result = processor.process_large_gdf(
            ...     large_gdf,
            ...     process_func=densify_points
            ... )
        """
        results = []

        # Calculate total number of chunks
        n_chunks = int(np.ceil(len(gdf) / self.chunk_size))

        for i in range(n_chunks):
            start_idx = i * self.chunk_size
            end_idx = min((i + 1) * self.chunk_size, len(gdf))

            # Extract chunk
            chunk = gdf.iloc[start_idx:end_idx].copy()

            # Process chunk
            processed_chunk = process_func(chunk)
            results.append(processed_chunk)

            # Show progress
            if show_progress:
                print(f"Processed chunk {i + 1}/{n_chunks}")

        # Combine results
        if results:
            return gpd.GeoDataFrame.pd.concat(results)
        else:
            return gdf.iloc[0:0]  # Empty GeoDataFrame


def auto_chunk_size(
    n_items: int,
    available_memory_mb: int = 1024,
    item_size_mb: float = 0.001
) -> int:
    """
    Automatically determine optimal chunk size.

    Args:
        n_items: Total number of items.
        available_memory_mb: Available memory in MB.
        item_size_mb: Estimated size per item in MB.

    Returns:
        Optimal chunk size.

    Example:
        >>> # 10000 items, 1GB memory, 10KB per item
        >>> chunk_size = auto_chunk_size(
        ...     n_items=10000,
        ...     available_memory_mb=1024,
        ...     item_size_mb=0.01
        ... )
        >>> print(f"Optimal chunk size: {chunk_size}")
    """
    # Calculate how many items fit in memory
    max_items_in_memory = int(available_memory_mb / item_size_mb)

    # Use 80% of available memory
    chunk_size = int(max_items_in_memory * 0.8)

    # But don't exceed total items
    chunk_size = min(chunk_size, n_items)

    # Minimum chunk size of 10
    chunk_size = max(chunk_size, 10)

    return chunk_size
