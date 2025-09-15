"""Backward compatibility layer for async operations.

This module provides synchronous wrappers for async operations,
maintaining 100% backward compatibility while enabling async optimization.
"""

import asyncio
import threading

from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

# Import module to allow unittest.patch on class reference to take effect
import claude_builder.core.async_analyzer as _async_analyzer_mod
from claude_builder.core.async_generator import AsyncDocumentGenerator
from claude_builder.core.async_template_manager import AsyncTemplateManager
from claude_builder.core.models import (
    GeneratedContent,
    ProjectAnalysis,
    ValidationResult,
)
from claude_builder.utils.async_performance import performance_monitor
from claude_builder.utils.exceptions import AnalysisError, PerformanceError


F = TypeVar("F", bound=Callable[..., Any])


class AsyncCompatibilityManager:
    """Manages async-to-sync compatibility layer."""

    def __init__(self) -> None:
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._async_analyzer: Optional[AsyncProjectAnalyzer] = None
        self._async_generator: Optional[AsyncDocumentGenerator] = None
        self._async_template_manager: Optional[AsyncTemplateManager] = None
        self._thread_pool_size = 4
        # Per-thread storage to avoid sharing async components across threads
        self._tls = threading.local()

    def _get_or_create_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop for sync operations in the current thread."""
        # Called only when not already inside an async context; safe to reuse or create
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            # No loop exists in this thread; create and set one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    def run_async_in_sync(self, coro: Any) -> Any:
        """Run async coroutine in sync context safely."""
        try:
            # Check if we're already in an async context
            try:
                asyncio.get_running_loop()
                # We're in an async context, need to handle differently
                return self._run_in_thread_pool(coro)
            except RuntimeError:
                # Not in async context, safe to use run_until_complete
                loop = self._get_or_create_loop()
                return loop.run_until_complete(coro)
        except PerformanceError:
            # Re-raise PerformanceErrors as-is
            raise
        except Exception as e:
            # Check if it's an expected exception type that should be re-raised
            if isinstance(e, (ValueError, RuntimeError, TypeError, AnalysisError)):
                raise
            # Only wrap unexpected exceptions
            raise PerformanceError(
                f"Failed to run async operation in sync context: {e}"
            ) from e

    def _run_in_thread_pool(self, coro: Any) -> Any:
        """Run coroutine in thread pool when already in async context."""
        import concurrent.futures

        def run_coro() -> Any:
            new_loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(new_loop)
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self._thread_pool_size
        ) as executor:
            future = executor.submit(run_coro)
            return future.result(timeout=300)  # 5 minute timeout

    def get_async_analyzer(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Get or create async analyzer instance.

        Instances are isolated per-thread to support concurrent operations
        in tests and real usage without cross-thread state leakage. Within a
        given thread and manager instance, the returned analyzer is stable
        (singleton behavior per thread).
        """
        analyzer = getattr(self._tls, "async_analyzer", None)
        if analyzer is None:
            analyzer = _async_analyzer_mod.AsyncProjectAnalyzer(config)
            setattr(self._tls, "async_analyzer", analyzer)
            # Maintain legacy attribute for compatibility with tests
            self._async_analyzer = analyzer
        return analyzer

    def new_async_analyzer(self, config: Optional[Dict[str, Any]] = None) -> Any:
        """Always create a fresh async analyzer instance.

        Does not cache into thread-local storage; used where tests expect the
        constructor to reflect current patching/mocking.
        """
        return _async_analyzer_mod.AsyncProjectAnalyzer(config)

    def reset_thread_analyzer(self) -> None:
        """Reset the thread-local analyzer instance (used by tests)."""
        if hasattr(self._tls, "async_analyzer"):
            delattr(self._tls, "async_analyzer")

    def get_async_generator(
        self, config: Optional[Dict[str, Any]] = None
    ) -> AsyncDocumentGenerator:
        """Get or create async generator instance (per-thread)."""
        generator = getattr(self._tls, "async_generator", None)
        if generator is None:
            generator = AsyncDocumentGenerator(config)
            setattr(self._tls, "async_generator", generator)
            self._async_generator = generator
        return generator

    def get_async_template_manager(
        self, config: Optional[Dict[str, Any]] = None
    ) -> AsyncTemplateManager:
        """Get or create async template manager instance (per-thread)."""
        manager = getattr(self._tls, "async_template_manager", None)
        if manager is None:
            manager = AsyncTemplateManager(config)
            setattr(self._tls, "async_template_manager", manager)
            self._async_template_manager = manager
        return manager

    def cleanup(self) -> None:
        """Clean up async resources."""

        async def cleanup_async() -> None:
            if self._async_template_manager:
                await self._async_template_manager.cleanup_async()

        if any(
            [self._async_analyzer, self._async_generator, self._async_template_manager]
        ):
            self.run_async_in_sync(cleanup_async())

        # Reset instances (legacy attributes) and thread-local ones for current thread
        self._async_analyzer = None
        self._async_generator = None
        self._async_template_manager = None
        for name in ("async_analyzer", "async_generator", "async_template_manager"):
            if hasattr(self._tls, name):
                delattr(self._tls, name)


# Global compatibility manager instance
_compat_manager = AsyncCompatibilityManager()


def async_to_sync(async_func: Callable) -> Callable:
    """Decorator to convert async function to sync with compatibility layer."""

    @wraps(async_func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        coro = async_func(*args, **kwargs)
        return _compat_manager.run_async_in_sync(coro)

    return sync_wrapper


class SyncProjectAnalyzerCompat:
    """Sync wrapper for AsyncProjectAnalyzer."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config
        _compat_manager.reset_thread_analyzer()
        self._async_analyzer = _compat_manager.get_async_analyzer(config)

    @async_to_sync
    async def analyze(self, project_path: Union[str, Path]) -> ProjectAnalysis:
        """Analyze project synchronously using async implementation."""
        return await self._async_analyzer.analyze_async(project_path)

    @async_to_sync
    async def batch_analyze(
        self, project_paths: List[Union[str, Path]]
    ) -> List[ProjectAnalysis]:
        """Batch analyze projects synchronously."""
        return await self._async_analyzer.batch_analyze_async(project_paths)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        analyzer = _compat_manager.get_async_analyzer(self.config)
        return analyzer.get_performance_stats()


class SyncDocumentGeneratorCompat:
    """Sync wrapper for AsyncDocumentGenerator."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config
        self._async_generator = _compat_manager.get_async_generator(config)

    @async_to_sync
    async def generate(
        self, analysis: ProjectAnalysis, output_path: Path
    ) -> GeneratedContent:
        """Generate documentation synchronously using async implementation."""
        return await self._async_generator.generate_async(analysis, output_path)

    @async_to_sync
    async def batch_generate(
        self, analyses: List[ProjectAnalysis], base_output_path: Path
    ) -> List[GeneratedContent]:
        """Batch generate documentation synchronously."""
        return await self._async_generator.batch_generate_async(
            analyses, base_output_path
        )

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return self._async_generator.get_performance_stats()


class SyncTemplateManagerCompat:
    """Sync wrapper for AsyncTemplateManager."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config
        self._async_template_manager = _compat_manager.get_async_template_manager(
            config
        )

    @async_to_sync
    async def get_template(
        self, template_name: str, analysis: Optional[ProjectAnalysis] = None
    ) -> Optional[Dict[str, Any]]:
        """Get template synchronously using async implementation."""
        return await self._async_template_manager.get_template_async(
            template_name, analysis
        )

    @async_to_sync
    async def validate_template(
        self, template_path: Union[str, Path]
    ) -> ValidationResult:
        """Validate template synchronously."""
        return await self._async_template_manager.validate_template_async(template_path)

    @async_to_sync
    async def install_template(
        self, template_source: str, destination: Optional[Path] = None
    ) -> Path:
        """Install template synchronously."""
        return await self._async_template_manager.install_template_async(
            template_source, destination
        )

    @async_to_sync
    async def list_templates(self, include_remote: bool = True) -> List[Dict[str, Any]]:
        """List templates synchronously."""
        return await self._async_template_manager.list_templates_async(include_remote)

    @async_to_sync
    async def search_templates(
        self, query: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search templates synchronously."""
        return await self._async_template_manager.search_templates_async(query, limit)

    @async_to_sync
    async def batch_process_templates(
        self, template_operations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Batch process templates synchronously."""
        return await self._async_template_manager.batch_process_templates_async(
            template_operations
        )

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return self._async_template_manager.get_performance_stats()


class PerformanceBenchmarker:
    """Performance benchmarking utilities for async vs sync comparison."""

    def __init__(self) -> None:
        self.benchmark_results: Dict[str, Dict[str, Any]] = {}

    def benchmark_operation(
        self,
        operation_name: str,
        async_func: Callable[..., Any],
        sync_func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Benchmark async vs sync operation performance."""
        import time

        results: Dict[str, Any] = {
            "operation": operation_name,
            "args_count": len(args),
            "kwargs_count": len(kwargs),
        }

        # Benchmark sync operation
        sync_start = time.perf_counter()
        try:
            sync_result = sync_func(*args, **kwargs)
            sync_end = time.perf_counter()
            results["sync"] = {
                "duration": sync_end - sync_start,
                "success": True,
                "result_type": type(sync_result).__name__,
            }
        except Exception as e:
            sync_end = time.perf_counter()
            results["sync"] = {
                "duration": sync_end - sync_start,
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }

        # Benchmark async operation
        async_start = time.perf_counter()
        try:
            async_result = _compat_manager.run_async_in_sync(
                async_func(*args, **kwargs)
            )
            async_end = time.perf_counter()
            results["async"] = {
                "duration": async_end - async_start,
                "success": True,
                "result_type": type(async_result).__name__,
            }
        except Exception as e:
            async_end = time.perf_counter()
            results["async"] = {
                "duration": async_end - async_start,
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }

        # Calculate performance improvement
        sync_result = results["sync"]
        async_result = results["async"]
        if (
            isinstance(sync_result, dict)
            and isinstance(async_result, dict)
            and sync_result["success"]
            and async_result["success"]
        ):
            sync_duration = sync_result["duration"]
            async_duration = async_result["duration"]

            if async_duration > 0:
                improvement = ((sync_duration - async_duration) / sync_duration) * 100
                results["performance_improvement_percent"] = improvement
                results["speedup_factor"] = (
                    sync_duration / async_duration if async_duration > 0 else 0
                )

        # Store results
        self.benchmark_results[operation_name] = results

        return results

    def get_benchmark_summary(self) -> Dict[str, Any]:
        """Get summary of all benchmark results."""
        if not self.benchmark_results:
            return {"message": "No benchmarks run yet"}

        successful_benchmarks = [
            result
            for result in self.benchmark_results.values()
            if result.get("performance_improvement_percent") is not None
        ]

        if not successful_benchmarks:
            return {"message": "No successful benchmarks with performance data"}

        improvements = [
            b["performance_improvement_percent"] for b in successful_benchmarks
        ]
        speedups = [b["speedup_factor"] for b in successful_benchmarks]

        return {
            "total_benchmarks": len(self.benchmark_results),
            "successful_benchmarks": len(successful_benchmarks),
            "average_improvement_percent": sum(improvements) / len(improvements),
            "max_improvement_percent": max(improvements),
            "min_improvement_percent": min(improvements),
            "average_speedup_factor": sum(speedups) / len(speedups),
            "max_speedup_factor": max(speedups),
            "operations": list(self.benchmark_results.keys()),
        }

    def run_comprehensive_benchmarks(
        self,
        project_path: Union[str, Path],
        template_name: str = "basic",
    ) -> Dict[str, Any]:
        """Run comprehensive benchmarks comparing async vs sync performance."""
        from claude_builder.core.analyzer import ProjectAnalyzer
        from claude_builder.core.template_manager import CoreTemplateManager

        # Create sync instances
        sync_analyzer = ProjectAnalyzer()
        sync_template_manager = CoreTemplateManager()

        # Create async compat instances
        async_analyzer = SyncProjectAnalyzerCompat()
        async_template_manager = SyncTemplateManagerCompat()

        # Benchmark project analysis
        self.benchmark_operation(
            "project_analysis",
            async_analyzer._async_analyzer.analyze_async,
            sync_analyzer.analyze,
            project_path,
        )

        # Benchmark template retrieval
        self.benchmark_operation(
            "template_retrieval",
            async_template_manager._async_template_manager.get_template_async,
            sync_template_manager.load_template,
            template_name,
        )

        # Benchmark template listing
        self.benchmark_operation(
            "template_listing",
            async_template_manager._async_template_manager.list_templates_async,
            list,  # Simplified sync version
        )

        return self.get_benchmark_summary()


# Global benchmarker instance
performance_benchmarker = PerformanceBenchmarker()


def cleanup_compatibility_layer() -> None:
    """Clean up the compatibility layer resources."""
    _compat_manager.cleanup()


def get_performance_overview() -> Dict[str, Any]:
    """Get comprehensive performance overview of async system."""
    return {
        "global_performance_monitor": performance_monitor.get_metrics(),
        "benchmark_summary": performance_benchmarker.get_benchmark_summary(),
        "async_analyzer_stats": (
            _compat_manager._async_analyzer.get_performance_stats()
            if _compat_manager._async_analyzer
            else None
        ),
        "async_generator_stats": (
            _compat_manager._async_generator.get_performance_stats()
            if _compat_manager._async_generator
            else None
        ),
        "async_template_manager_stats": (
            _compat_manager._async_template_manager.get_performance_stats()
            if _compat_manager._async_template_manager
            else None
        ),
    }
