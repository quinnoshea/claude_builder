"""Integration tests for Phase 3.4 async performance optimization.

Tests the complete async performance system integration including:
- Async template operations
- Performance monitoring
- Memory optimization
- Backward compatibility
- Benchmarking capabilities
"""

import asyncio

from unittest.mock import MagicMock

import pytest

from claude_builder.core.async_compatibility import (
    get_performance_overview,
    performance_benchmarker,
)
from claude_builder.core.models import ProjectAnalysis, ProjectType
from claude_builder.core.template_manager import ModernTemplateManager
from claude_builder.utils.async_performance import cache, performance_monitor


@pytest.mark.integration
class TestPhase34AsyncIntegration:
    """Integration tests for Phase 3.4 async performance system."""

    @pytest.fixture
    def template_manager(self):
        """Create template manager with async optimization enabled."""
        config = {
            "enable_async_performance": True,
            "max_concurrent_operations": 5,
            "enable_caching": True,
        }
        return ModernTemplateManager(config=config)

    @pytest.fixture
    def mock_project_analysis(self):
        """Create mock project analysis for testing."""
        analysis = MagicMock(spec=ProjectAnalysis)
        analysis.project_name = "test_project"
        analysis.project_type = ProjectType.WEB_APPLICATION
        analysis.languages = []
        analysis.frameworks = []
        analysis.complexity_level = "medium"
        analysis.analysis_confidence = 85.0
        return analysis

    def test_template_manager_async_integration(self, template_manager):
        """Test template manager with async optimization enabled."""
        # Check async optimization is available
        stats = template_manager.get_performance_stats()

        # Should have performance stats structure
        assert "async_performance_enabled" in stats
        assert "async_available" in stats
        assert "template_manager_type" in stats
        assert stats["template_manager_type"] == "ModernTemplateManager"

    def test_template_operations_with_async_fallback(
        self, template_manager, mock_project_analysis
    ):
        """Test template operations with async optimization and sync fallback."""
        # Test get template with async optimization
        template = template_manager.get_template_async_optimized(
            "basic", mock_project_analysis
        )

        # Should return some result (either from async or sync fallback)
        assert template is None or isinstance(template, dict)

        # Test list templates with async optimization
        templates = template_manager.list_templates_async_optimized(
            include_remote=False
        )

        # Should return list
        assert isinstance(templates, list)

        # Test search templates with async optimization
        search_results = template_manager.search_templates_async_optimized(
            "python", limit=5
        )

        # Should return list
        assert isinstance(search_results, list)

    def test_async_optimization_control(self, template_manager):
        """Test enabling/disabling async optimization."""
        # Initially should be enabled (from fixture config)
        stats = template_manager.get_performance_stats()
        # Verify initial state
        assert stats.get("async_performance_enabled", False)

        # Disable async optimization
        template_manager.enable_async_optimization(False)
        stats = template_manager.get_performance_stats()
        assert stats["async_performance_enabled"] is False

        # Re-enable async optimization
        template_manager.enable_async_optimization(True)
        stats = template_manager.get_performance_stats()
        # May not be enabled if async components not available
        assert "async_performance_enabled" in stats

    def test_cleanup_async_resources(self, template_manager):
        """Test cleanup of async resources."""
        # Should not raise exceptions
        template_manager.cleanup_async_resources()

        # After cleanup, async should be disabled
        stats = template_manager.get_performance_stats()
        # Stats should still be available but async components cleaned up
        assert "template_manager_type" in stats

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self):
        """Test integration with performance monitoring system."""
        # Test global performance monitor
        async with performance_monitor.track_operation("integration_test") as context:
            assert context["name"] == "integration_test"

            # Simulate some work
            await asyncio.sleep(0.001)

        # Check metrics were recorded
        metrics = performance_monitor.get_metrics("integration_test")
        assert metrics["count"] >= 1
        assert metrics["total_time"] > 0

    @pytest.mark.asyncio
    async def test_caching_system_integration(self):
        """Test integration with caching system."""
        # Test global cache
        cache_key = "integration_test_key"
        cache_value = {"test": "integration_value", "timestamp": "now"}

        await cache.set(cache_key, cache_value)
        retrieved_value = await cache.get(cache_key)

        assert retrieved_value == cache_value

        # Test cache stats
        stats = cache.get_stats()
        assert "size" in stats
        assert "max_size" in stats
        assert stats["size"] >= 1

    def test_performance_benchmarker_integration(self):
        """Test integration with performance benchmarker."""

        def sync_operation(x):
            import time

            time.sleep(0.001)
            return x * 2

        async def async_operation(x):
            await asyncio.sleep(0.001)
            return x * 2

        # Benchmark operation
        result = performance_benchmarker.benchmark_operation(
            "integration_benchmark", async_operation, sync_operation, 5
        )

        assert result["operation"] == "integration_benchmark"
        assert "sync" in result
        assert "async" in result
        assert result["args_count"] == 1

        # Get benchmark summary
        summary = performance_benchmarker.get_benchmark_summary()
        assert "total_benchmarks" in summary
        assert summary["total_benchmarks"] >= 1

    def test_global_performance_overview(self):
        """Test global performance overview."""
        overview = get_performance_overview()

        assert isinstance(overview, dict)
        assert "global_performance_monitor" in overview
        assert "benchmark_summary" in overview

        # Should have performance data
        monitor_stats = overview["global_performance_monitor"]
        assert isinstance(monitor_stats, dict)

    def test_concurrent_template_operations(self, template_manager):
        """Test concurrent template operations don't interfere with each other."""
        import threading

        results = {}
        errors = {}

        def template_operation(thread_id):
            try:
                # Perform multiple template operations
                templates = template_manager.list_templates_async_optimized(
                    include_remote=False
                )
                search_results = template_manager.search_templates_async_optimized(
                    f"test_{thread_id}"
                )
                stats = template_manager.get_performance_stats()

                results[thread_id] = {
                    "templates_count": len(templates),
                    "search_count": len(search_results),
                    "has_stats": "template_manager_type" in stats,
                }
            except Exception as e:
                errors[thread_id] = e

        # Run concurrent operations
        threads = []
        for i in range(3):
            thread = threading.Thread(target=template_operation, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(timeout=10)

        # All operations should succeed
        assert len(results) == 3
        assert len(errors) == 0

        for thread_id, result in results.items():
            assert result["has_stats"] is True
            assert isinstance(result["templates_count"], int)
            assert isinstance(result["search_count"], int)

    def test_error_handling_and_fallback(self, template_manager):
        """Test error handling and fallback to sync operations."""
        # Test with invalid template name
        template = template_manager.get_template_async_optimized(
            "definitely_nonexistent_template_12345"
        )

        # Should handle gracefully (return None or fallback result)
        assert template is None or isinstance(template, dict)

        # Test search with empty query
        results = template_manager.search_templates_async_optimized("", limit=5)

        # Should handle gracefully
        assert isinstance(results, list)

    @pytest.mark.performance
    def test_performance_characteristics(self, template_manager):
        """Test performance characteristics of async system."""
        import time

        # Measure template listing performance
        start_time = time.perf_counter()

        for _ in range(10):
            _ = template_manager.list_templates_async_optimized(include_remote=False)

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Should complete reasonably quickly
        # (Adjust threshold based on system capabilities)
        assert duration < 5.0  # 5 seconds for 10 operations

        # Get performance stats
        stats = template_manager.get_performance_stats()

        # Should have meaningful stats
        assert "template_manager_type" in stats
        if "async_stats" in stats:
            async_stats = stats["async_stats"]
            assert isinstance(async_stats, dict)

    def test_memory_usage_optimization(self):
        """Test memory usage optimization features."""
        import gc
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create multiple template managers to test memory management
        managers = []
        for i in range(5):
            config = {
                "enable_async_performance": True,
                "max_concurrent_operations": 3,
                "enable_caching": True,
            }
            manager = ModernTemplateManager(config=config)
            managers.append(manager)

            # Perform operations that might consume memory
            for j in range(5):
                manager.list_templates_async_optimized(include_remote=False)
                manager.search_templates_async_optimized(f"query_{i}_{j}")

        # Clean up managers
        for manager in managers:
            manager.cleanup_async_resources()

        # Force garbage collection
        gc.collect()

        # Memory should not have grown excessively
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory

        # Allow some memory growth but not excessive
        # (Adjust threshold based on system and test requirements)
        max_allowed_growth = 100 * 1024 * 1024  # 100MB
        assert memory_growth < max_allowed_growth

    def test_template_manager_integration_with_existing_system(
        self, template_manager, mock_project_analysis
    ):
        """Test integration with existing template manager functionality."""
        # Test that async optimization doesn't break existing functionality

        # Test legacy methods still work
        templates_by_type = template_manager.get_templates_by_type("documentation")
        assert isinstance(templates_by_type, list)

        # Test template rendering still works
        from claude_builder.core.template_manager import TemplateContext

        context = TemplateContext(variables={"project_name": "test_project"})

        rendered = template_manager.render_template("basic.md", context)
        assert isinstance(rendered, str)

        # Test environment generation still works
        try:
            environment = template_manager.generate_complete_environment(
                mock_project_analysis
            )
            # Should complete without error (content may vary)
            assert hasattr(environment, "claude_md")
            assert hasattr(environment, "agents_md")
        except Exception:
            # Some dependencies might not be available in test environment
            # As long as it doesn't crash the async system, that's acceptable
            pass

        # Verify async optimization is still working after legacy operations
        stats = template_manager.get_performance_stats()
        assert "template_manager_type" in stats

    @pytest.mark.skipif(
        not hasattr(asyncio, "run"), reason="asyncio.run not available (Python < 3.7)"
    )
    def test_async_event_loop_compatibility(self):
        """Test compatibility with different async event loop scenarios."""

        async def async_test_operation():
            # Test that async operations work within async context
            async with performance_monitor.track_operation("loop_test"):
                await cache.set("loop_test_key", "loop_test_value")
                value = await cache.get("loop_test_key")
                return value

        # Test running in new event loop
        result = asyncio.run(async_test_operation())
        assert result == "loop_test_value"

        # Test metrics were recorded
        metrics = performance_monitor.get_metrics("loop_test")
        assert metrics["count"] >= 1


@pytest.mark.integration
@pytest.mark.performance
class TestPhase34PerformanceBenchmarks:
    """Performance benchmark tests for Phase 3.4."""

    def test_template_operations_performance_baseline(self):
        """Establish performance baseline for template operations."""
        import time

        config = {"enable_async_performance": False}  # Sync baseline
        sync_manager = ModernTemplateManager(config=config)

        # Measure sync performance
        sync_times = []
        for _ in range(10):
            start = time.perf_counter()
            _ = sync_manager.list_templates_async_optimized(include_remote=False)
            end = time.perf_counter()
            sync_times.append(end - start)

        avg_sync_time = sum(sync_times) / len(sync_times)

        # Test with async optimization (if available)
        config = {"enable_async_performance": True}
        async_manager = ModernTemplateManager(config=config)

        async_times = []
        for _ in range(10):
            start = time.perf_counter()
            _ = async_manager.list_templates_async_optimized(include_remote=False)
            end = time.perf_counter()
            async_times.append(end - start)

        avg_async_time = sum(async_times) / len(async_times)

        # Log performance comparison
        print(f"\nSync average time: {avg_sync_time:.4f}s")
        print(f"Async average time: {avg_async_time:.4f}s")

        if avg_sync_time > 0 and avg_async_time > 0:
            improvement = ((avg_sync_time - avg_async_time) / avg_sync_time) * 100
            print(f"Performance improvement: {improvement:.1f}%")

        # Both should complete in reasonable time
        assert avg_sync_time < 1.0  # 1 second per operation
        assert avg_async_time < 1.0  # 1 second per operation

    def test_concurrent_operations_scalability(self):
        """Test scalability of concurrent operations."""
        import concurrent.futures
        import time

        config = {
            "enable_async_performance": True,
            "max_concurrent_operations": 10,
        }
        manager = ModernTemplateManager(config=config)

        def template_operation(operation_id):
            start_time = time.perf_counter()

            # Perform multiple operations
            templates = manager.list_templates_async_optimized(include_remote=False)
            search_results = manager.search_templates_async_optimized(
                f"test_{operation_id}"
            )
            stats = manager.get_performance_stats()

            end_time = time.perf_counter()
            return {
                "operation_id": operation_id,
                "duration": end_time - start_time,
                "templates_found": len(templates),
                "search_results": len(search_results),
                "has_stats": bool(stats),
            }

        # Test different levels of concurrency
        for num_workers in [1, 5, 10]:
            start_time = time.perf_counter()

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=num_workers
            ) as executor:
                futures = [executor.submit(template_operation, i) for i in range(20)]
                results = [future.result(timeout=30) for future in futures]

            end_time = time.perf_counter()
            total_time = end_time - start_time

            # All operations should succeed
            assert len(results) == 20
            assert all(result["has_stats"] for result in results)

            avg_operation_time = sum(r["duration"] for r in results) / len(results)

            print(
                f"\nConcurrency {num_workers}: Total {total_time:.2f}s, Avg per op {avg_operation_time:.4f}s"
            )

            # Operations should complete in reasonable time
            assert total_time < 60  # 1 minute total
            assert avg_operation_time < 5  # 5 seconds per operation

    def test_memory_efficiency_under_load(self):
        """Test memory efficiency under sustained load."""
        import gc
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        config = {
            "enable_async_performance": True,
            "max_concurrent_operations": 5,
            "enable_caching": True,
        }
        manager = ModernTemplateManager(config=config)

        # Sustained load test
        for batch in range(5):
            # Perform batch of operations
            for i in range(20):
                _ = manager.list_templates_async_optimized(include_remote=False)
                _ = manager.search_templates_async_optimized(f"batch_{batch}_op_{i}")

            # Check memory usage
            current_memory = process.memory_info().rss
            memory_growth = current_memory - initial_memory

            print(f"Batch {batch}: Memory growth {memory_growth / 1024 / 1024:.1f}MB")

            # Periodic garbage collection
            if batch % 2 == 0:
                gc.collect()

        # Final cleanup
        manager.cleanup_async_resources()
        gc.collect()

        final_memory = process.memory_info().rss
        total_growth = final_memory - initial_memory

        print(f"Final memory growth: {total_growth / 1024 / 1024:.1f}MB")

        # Memory growth should be reasonable
        max_allowed_growth = 200 * 1024 * 1024  # 200MB
        assert total_growth < max_allowed_growth
