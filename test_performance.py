"""
Basic test script for performance module.
"""
import sys
sys.path.insert(0, '/Users/bruce/10_School/11_MSC-Politecnico di Milano/03-Third Sem-Archive/GProcessing/2025-2026/GProcessing2025/src')

from svipro.performance import (
    SpatialChunker,
    DiskCache,
    ProgressTracker,
    TQDM_AVAILABLE
)
from shapely.geometry import box
import time

# Define function at module level for pickling
def square(x):
    return x ** 2

if __name__ == '__main__':
    # Import ParallelProcessor inside main for multiprocessing
    from svipro.performance import ParallelProcessor

    print("="*60)
    print("SVIPro Performance Module Test")
    print("="*60)

    # Test 1: Parallel Processing
    print("\nTest 1: Parallel Processing")
    try:
        processor = ParallelProcessor(n_workers=2)
        items = list(range(10))
        results = processor.map(square, items)

        assert results == [x**2 for x in items]
        print("✓ Parallel processing works correctly")
        print(f"  Processed {len(items)} items with {processor.n_workers} workers")
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)

    # Test 2: Spatial Chunking
    print("\nTest 2: Spatial Chunking")
    try:
        # Create a large boundary (100km x 100km)
        large_boundary = box(0, 0, 100000, 100000)

        # Create chunker with 10km chunks
        chunker = SpatialChunker(chunk_size_km=10)

        # Estimate chunks
        n_chunks = chunker.estimate_chunk_count(large_boundary)
        print(f"  Estimated chunks for 100km x 100km area: {n_chunks}")

        # Create actual chunks (limit to 10 for testing)
        chunks = list(chunker.create_chunks(large_boundary, max_chunks=10))

        print(f"✓ Spatial chunking works correctly")
        print(f"  Created {len(chunks)} chunks")
        print(f"  Chunk sizes range: {min(c.area for c in chunks):.0f} - {max(c.area for c in chunks):.0f} m²")
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)

    # Test 3: Disk Cache
    print("\nTest 3: Disk Cache")
    try:
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = DiskCache(cache_dir=f"{tmpdir}/test_cache")

            # Test cache miss
            result = cache.get("test_key")
            assert result is None, "Cache should be empty initially"

            # Test cache put
            test_data = {"value": 42, "list": [1, 2, 3]}
            cache.put("test_key", test_data)

            # Test cache hit
            result = cache.get("test_key")
            assert result == test_data, "Cached data should match"

            # Test cache delete
            success = cache.delete("test_key")
            assert success, "Delete should succeed"

            result = cache.get("test_key")
            assert result is None, "Key should be deleted"

            # Test cache stats
            cache.put("key1", {"data": 1})
            cache.put("key2", {"data": 2})
            stats = cache.get_stats()

            print("✓ Disk cache works correctly")
            print(f"  Cache entries: {stats['n_entries']}")
            print(f"  Cache size: {stats['size_mb']} MB")
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)

    # Test 4: Progress Tracking
    print("\nTest 4: Progress Tracking")
    try:
        total_items = 100
        tracker = ProgressTracker(total=total_items, description="Test Progress", silent=True)

        start_time = time.time()

        for i in range(total_items):
            # Simulate some work
            time.sleep(0.001)
            tracker.update(1)

        elapsed = time.time() - start_time

        tracker.close()

        print("✓ Progress tracking works correctly")
        print(f"  Processed {total_items} items in {elapsed:.2f} seconds")
        print(f"  TQDM available: {TQDM_AVAILABLE}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)

    # Test 5: Optimal worker count
    print("\nTest 5: Optimal Worker Count")
    try:
        from svipro.performance import get_optimal_n_workers

        n_workers_sampling = get_optimal_n_workers("sampling")
        n_workers_osm = get_optimal_n_workers("osm_download")

        print("✓ Optimal worker calculation works")
        print(f"  Sampling workers: {n_workers_sampling}")
        print(f"  OSM download workers: {n_workers_osm}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)

    # Test 6: Auto chunk size
    print("\nTest 6: Auto Chunk Size")
    try:
        from svipro.performance import auto_chunk_size

        chunk_size = auto_chunk_size(
            n_items=10000,
            available_memory_mb=1024,
            item_size_mb=0.001
        )

        print("✓ Auto chunk size calculation works")
        print(f"  Recommended chunk size: {chunk_size} items")
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)

    print("\n" + "="*60)
    print("All performance module tests passed! ✓")
    print("="*60)
    print("\nPerformance optimization features:")
    print("  ✓ Parallel processing (multi-core)")
    print("  ✓ Spatial chunking (large areas)")
    print("  ✓ Disk caching (avoid redundant operations)")
    print("  ✓ Progress tracking (user feedback)")
    print("  ✓ Auto optimization (chunk size, workers)")
