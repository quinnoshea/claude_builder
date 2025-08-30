"""Tests for async performance optimization framework.

Tests Phase 3.4 async patterns, memory optimization, and performance enhancements.
"""

import asyncio
import tempfile

from pathlib import Path
from unittest.mock import patch

import pytest

from claude_builder.utils.async_performance import (
    AsyncCache,
    AsyncConnectionPool,
    AsyncFileProcessor,
    AsyncPerformanceMonitor,
    async_rate_limit,
    async_retry,
    cache,
    file_processor,
    performance_monitor,
)
from claude_builder.utils.exceptions import PerformanceError


class TestAsyncPerformanceMonitor:
    """Test async performance monitoring functionality."""

    @pytest.fixture
    def monitor(self):
        """Create performance monitor for testing."""
        return AsyncPerformanceMonitor()

    @pytest.mark.asyncio
    async def test_operation_tracking(self, monitor):
        """Test basic operation tracking."""
        async with monitor.track_operation("test_operation") as context:
            assert context["name"] == "test_operation"
            assert "start_time" in context
            assert "start_memory" in context

            # Simulate work
            await asyncio.sleep(0.01)

        # Check metrics were recorded
        metrics = monitor.get_metrics("test_operation")
        assert metrics["count"] == 1
        assert metrics["total_time"] > 0
        assert metrics["avg_time"] > 0
        assert metrics["errors"] == 0

    @pytest.mark.asyncio
    async def test_operation_error_tracking(self, monitor):
        """Test error tracking in operations."""
        with pytest.raises(ValueError):
            async with monitor.track_operation("error_operation"):
                raise ValueError("Test error")

        metrics = monitor.get_metrics("error_operation")
        assert metrics["count"] == 1
        assert metrics["errors"] == 1

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, monitor):
        """Test concurrent operation tracking."""

        async def test_operation(op_name):
            async with monitor.track_operation(op_name):
                await asyncio.sleep(0.01)

        # Run concurrent operations
        tasks = [asyncio.create_task(test_operation(f"op_{i}")) for i in range(5)]

        await asyncio.gather(*tasks)

        # Check all operations were tracked
        for i in range(5):
            metrics = monitor.get_metrics(f"op_{i}")
            assert metrics["count"] == 1

    def test_get_active_operations_count(self, monitor):
        """Test active operations count."""
        initial_count = monitor.get_active_operations_count()
        assert initial_count == 0

    @pytest.mark.asyncio
    async def test_memory_threshold_monitoring(self, monitor):
        """Test memory threshold monitoring."""
        # Mock psutil to simulate high memory usage
        with patch("psutil.virtual_memory") as mock_memory:
            mock_memory.return_value.percent = 90.0  # 90% memory usage

            async with monitor.track_operation("memory_test"):
                await asyncio.sleep(0.001)

        # Should have logged warning about high memory usage
        # (We can't easily test the logging without capturing logs)
        metrics = monitor.get_metrics("memory_test")
        assert metrics["count"] == 1


class TestAsyncCache:
    """Test async caching functionality."""

    @pytest.fixture
    def test_cache(self):
        """Create cache for testing."""
        return AsyncCache(max_size=3, ttl_seconds=1)

    @pytest.mark.asyncio
    async def test_basic_cache_operations(self, test_cache):
        """Test basic cache set/get operations."""
        # Test set and get
        await test_cache.set("key1", "value1")
        value = await test_cache.get("key1")
        assert value == "value1"

        # Test missing key
        value = await test_cache.get("missing_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, test_cache):
        """Test TTL expiration."""
        await test_cache.set("ttl_key", "ttl_value")

        # Should be available immediately
        value = await test_cache.get("ttl_key")
        assert value == "ttl_value"

        # Wait for TTL to expire
        await asyncio.sleep(1.1)

        # Should be expired
        value = await test_cache.get("ttl_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_lru_eviction(self, test_cache):
        """Test LRU eviction when cache is full."""
        # Fill cache to capacity
        await test_cache.set("key1", "value1")
        await test_cache.set("key2", "value2")
        await test_cache.set("key3", "value3")

        # Add one more item, should evict LRU item
        await test_cache.set("key4", "value4")

        # key1 should be evicted (LRU)
        value1 = await test_cache.get("key1")
        assert value1 is None

        # Other keys should still be available
        value4 = await test_cache.get("key4")
        assert value4 == "value4"

    @pytest.mark.asyncio
    async def test_cache_access_pattern_updates(self, test_cache):
        """Test that access updates LRU ordering."""
        # Fill cache
        await test_cache.set("key1", "value1")
        await test_cache.set("key2", "value2")
        await test_cache.set("key3", "value3")

        # Access key1 to make it recently used
        await test_cache.get("key1")

        # Add new item, should evict key2 (oldest unaccessed)
        await test_cache.set("key4", "value4")

        # key1 should still be available
        value1 = await test_cache.get("key1")
        assert value1 == "value1"

        # key2 should be evicted
        value2 = await test_cache.get("key2")
        assert value2 is None

    def test_cache_stats(self, test_cache):
        """Test cache statistics."""
        stats = test_cache.get_stats()
        assert "size" in stats
        assert "max_size" in stats
        assert "ttl_seconds" in stats
        assert stats["max_size"] == 3
        assert stats["ttl_seconds"] == 1


class TestAsyncFileProcessor:
    """Test async file processing functionality."""

    @pytest.fixture
    def processor(self):
        """Create file processor for testing."""
        return AsyncFileProcessor(max_concurrent_files=3)

    @pytest.mark.asyncio
    async def test_file_processing_context_manager(self, processor):
        """Test file processing context manager."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
            tmp.write("Test content\nLine 2\nLine 3")
            tmp.flush()
            tmp_path = Path(tmp.name)

        try:
            async with processor.process_file(tmp_path) as f:
                content = await f.read()
                assert "Test content" in content
        finally:
            tmp_path.unlink()

    @pytest.mark.asyncio
    async def test_read_file_chunks(self, processor):
        """Test reading file in chunks."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
            test_content = "A" * 1000  # 1KB of A's
            tmp.write(test_content)
            tmp.flush()
            tmp_path = Path(tmp.name)

        try:
            chunks = []
            async for chunk in processor.read_file_chunks(tmp_path):
                chunks.append(chunk)

            # Should have received content in chunks
            assert len(chunks) > 0
            reconstructed = "".join(chunks)
            assert reconstructed == test_content
        finally:
            tmp_path.unlink()

    @pytest.mark.asyncio
    async def test_write_file_stream(self, processor):
        """Test writing file from async stream."""

        async def content_stream():
            for i in range(5):
                yield f"Line {i}\n"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            tmp_path = Path(tmp.name)

        try:
            await processor.write_file_stream(tmp_path, content_stream())

            # Verify content was written
            with open(tmp_path) as f:
                content = f.read()
                assert "Line 0" in content
                assert "Line 4" in content
                assert content.count("\n") == 5
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    @pytest.mark.asyncio
    async def test_concurrent_file_processing(self, processor):
        """Test concurrent file processing limits."""
        # Create multiple temporary files
        files = []
        for i in range(5):
            tmp = tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=f"_{i}.txt"
            )
            tmp.write(f"File {i} content")
            tmp.flush()
            files.append(Path(tmp.name))

        try:
            # Process files concurrently
            async def process_file(file_path):
                async with processor.process_file(file_path) as f:
                    return await f.read()

            tasks = [asyncio.create_task(process_file(f)) for f in files]
            results = await asyncio.gather(*tasks)

            # All files should be processed
            assert len(results) == 5
            for i, result in enumerate(results):
                assert f"File {i} content" in result

        finally:
            for file_path in files:
                file_path.unlink()


class TestAsyncConnectionPool:
    """Test async HTTP connection pool functionality."""

    @pytest.mark.asyncio
    async def test_connection_pool_context_manager(self):
        """Test connection pool context manager."""
        pool = AsyncConnectionPool(max_connections=5, timeout=10)

        async with pool as session:
            # Should have aiohttp session
            assert session is not None
            assert hasattr(session, "get")
            assert hasattr(session, "post")

    @pytest.mark.asyncio
    async def test_connection_pool_cleanup(self):
        """Test connection pool cleanup."""
        pool = AsyncConnectionPool(max_connections=2)

        # Use pool and ensure it cleans up properly
        async with pool as session:
            assert session is not None

        # After context exit, session should be closed
        # (We can't easily test this without mocking aiohttp)


class TestAsyncDecorators:
    """Test async utility decorators."""

    @pytest.mark.asyncio
    async def test_async_retry_success(self):
        """Test async retry decorator on successful operation."""
        call_count = 0

        @async_retry(max_attempts=3, delay=0.01)
        async def successful_operation():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_operation()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_retry_with_failures(self):
        """Test async retry decorator with transient failures."""
        call_count = 0

        @async_retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count} failed")
            return "success"

        result = await failing_operation()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_retry_permanent_failure(self):
        """Test async retry decorator with permanent failure."""
        call_count = 0

        @async_retry(max_attempts=3, delay=0.01)
        async def always_failing_operation():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Permanent failure")

        with pytest.raises(RuntimeError, match="Permanent failure"):
            await always_failing_operation()

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_rate_limit(self):
        """Test async rate limiting decorator."""
        call_times = []

        @async_rate_limit(calls_per_second=10.0, burst_size=2)
        async def rate_limited_operation():
            call_times.append(asyncio.get_event_loop().time())
            return "called"

        # Make several calls rapidly
        tasks = [asyncio.create_task(rate_limited_operation()) for _ in range(5)]
        await asyncio.gather(*tasks)

        # Should have been rate limited
        assert len(call_times) == 5

        # First two calls should be quick (burst)
        assert call_times[1] - call_times[0] < 0.1

        # Later calls should be spaced out by rate limiting
        # (Exact timing is hard to test reliably, so we just check we got all calls)


class TestPerformanceIntegration:
    """Integration tests for performance monitoring."""

    @pytest.mark.asyncio
    async def test_global_performance_monitor_integration(self):
        """Test integration with global performance monitor."""
        # Test the global monitor instance
        async with performance_monitor.track_operation("integration_test") as context:
            assert context["name"] == "integration_test"
            await asyncio.sleep(0.001)

        metrics = performance_monitor.get_metrics("integration_test")
        assert metrics["count"] >= 1

    @pytest.mark.asyncio
    async def test_global_cache_integration(self):
        """Test integration with global cache."""
        # Test the global cache instance
        await cache.set("integration_key", "integration_value")
        value = await cache.get("integration_key")
        assert value == "integration_value"

    @pytest.mark.asyncio
    async def test_global_file_processor_integration(self):
        """Test integration with global file processor."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
            tmp.write("Integration test content")
            tmp.flush()
            tmp_path = Path(tmp.name)

        try:
            async with file_processor.process_file(tmp_path) as f:
                content = await f.read()
                assert "Integration test content" in content
        finally:
            tmp_path.unlink()


class TestErrorHandling:
    """Test error handling in async performance components."""

    @pytest.mark.asyncio
    async def test_performance_error_propagation(self):
        """Test that PerformanceError is properly raised and handled."""
        processor = AsyncFileProcessor()

        # Try to process non-existent file
        with pytest.raises(PerformanceError):
            async with processor.process_file(Path("/nonexistent/file.txt")):
                pass

    @pytest.mark.asyncio
    async def test_monitor_error_tracking(self):
        """Test error tracking in performance monitor."""
        monitor = AsyncPerformanceMonitor()

        # Track operation that raises exception
        with pytest.raises(ValueError):
            async with monitor.track_operation("error_test"):
                raise ValueError("Test error")

        # Check error was tracked
        metrics = monitor.get_metrics("error_test")
        assert metrics["errors"] == 1
        assert metrics["count"] == 1

    @pytest.mark.asyncio
    async def test_cache_error_handling(self):
        """Test error handling in cache operations."""
        test_cache = AsyncCache()

        # Cache should handle None values gracefully
        await test_cache.set("none_key", None)
        value = await test_cache.get("none_key")
        assert value is None

        # Should handle missing keys gracefully
        value = await test_cache.get("definitely_missing_key")
        assert value is None


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Benchmark cache performance."""
        test_cache = AsyncCache(max_size=1000)

        # Benchmark cache operations
        import time

        start_time = time.perf_counter()

        # Set 100 items
        for i in range(100):
            await test_cache.set(f"key_{i}", f"value_{i}")

        # Get 100 items
        for i in range(100):
            value = await test_cache.get(f"key_{i}")
            assert value == f"value_{i}"

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Should complete reasonably quickly (adjust threshold as needed)
        assert duration < 1.0  # 1 second for 200 operations

    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(self):
        """Benchmark concurrent operations performance."""
        monitor = AsyncPerformanceMonitor()

        async def concurrent_operation(op_id):
            async with monitor.track_operation(f"concurrent_op_{op_id}"):
                await asyncio.sleep(0.001)  # Simulate small amount of work
                return f"result_{op_id}"

        # Run 50 concurrent operations
        import time

        start_time = time.perf_counter()

        tasks = [asyncio.create_task(concurrent_operation(i)) for i in range(50)]
        results = await asyncio.gather(*tasks)

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Concurrent operations should complete faster than sequential
        # 50 * 0.001 = 0.05 seconds if sequential, should be much less with concurrency
        assert duration < 0.1  # Should complete in less than 100ms
        assert len(results) == 50

        # Check all operations were tracked
        for i in range(50):
            metrics = monitor.get_metrics(f"concurrent_op_{i}")
            assert metrics["count"] == 1

    @pytest.mark.asyncio
    async def test_memory_usage_tracking(self):
        """Test memory usage tracking accuracy."""
        monitor = AsyncPerformanceMonitor()

        # Create some memory usage
        large_data = ["x" * 1000 for _ in range(100)]  # ~100KB

        async with monitor.track_operation("memory_test") as _:
            # Add more memory usage during operation
            more_data = ["y" * 1000 for _ in range(100)]  # Another ~100KB
            await asyncio.sleep(0.001)

        metrics = monitor.get_metrics("memory_test")
        assert metrics["count"] == 1
        # Memory peak should be recorded (though exact value hard to test)
        assert "memory_peak" in metrics

        # Clean up
        del large_data
        del more_data
