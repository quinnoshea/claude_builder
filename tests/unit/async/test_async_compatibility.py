"""Tests for async compatibility layer.

Tests the backward compatibility wrappers and performance benchmarking.
"""

import asyncio
import tempfile

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from claude_builder.core.async_compatibility import (
    AsyncCompatibilityManager,
    PerformanceBenchmarker,
    SyncProjectAnalyzerCompat,
    SyncTemplateManagerCompat,
    async_to_sync,
    cleanup_compatibility_layer,
    get_performance_overview,
    performance_benchmarker,
)
from claude_builder.core.models import ProjectAnalysis, ProjectType
from claude_builder.utils.exceptions import PerformanceError


class TestAsyncCompatibilityManager:
    """Test async compatibility manager functionality."""

    @pytest.fixture
    def compat_manager(self):
        """Create compatibility manager for testing."""
        return AsyncCompatibilityManager()

    def test_get_async_analyzer(self, compat_manager):
        """Test getting async analyzer instance."""
        analyzer1 = compat_manager.get_async_analyzer()
        analyzer2 = compat_manager.get_async_analyzer()

        # Should return same instance (singleton behavior)
        assert analyzer1 is analyzer2
        assert analyzer1 is not None

    def test_get_async_generator(self, compat_manager):
        """Test getting async generator instance."""
        generator1 = compat_manager.get_async_generator()
        generator2 = compat_manager.get_async_generator()

        # Should return same instance (singleton behavior)
        assert generator1 is generator2
        assert generator1 is not None

    def test_get_async_template_manager(self, compat_manager):
        """Test getting async template manager instance."""
        manager1 = compat_manager.get_async_template_manager()
        manager2 = compat_manager.get_async_template_manager()

        # Should return same instance (singleton behavior)
        assert manager1 is manager2
        assert manager1 is not None

    def test_run_async_in_sync_simple(self, compat_manager):
        """Test running simple async operation in sync context."""

        async def simple_async_func():
            return "async_result"

        result = compat_manager.run_async_in_sync(simple_async_func())
        assert result == "async_result"

    def test_run_async_in_sync_with_exception(self, compat_manager):
        """Test running async operation that raises exception."""

        async def failing_async_func():
            raise ValueError("Async error")

        with pytest.raises(ValueError, match="Async error"):
            compat_manager.run_async_in_sync(failing_async_func())

    @pytest.mark.asyncio
    async def test_run_async_in_async_context(self, compat_manager):
        """Test running async operation when already in async context."""

        async def nested_async_func():
            await asyncio.sleep(0.001)
            return "nested_result"

        # This should handle being called from async context
        result = compat_manager.run_async_in_sync(nested_async_func())
        assert result == "nested_result"

    def test_cleanup(self, compat_manager):
        """Test cleanup of async resources."""
        # Initialize some components
        compat_manager.get_async_analyzer()
        compat_manager.get_async_generator()
        compat_manager.get_async_template_manager()

        # Cleanup should not raise exceptions
        compat_manager.cleanup()

        # Components should be reset
        assert compat_manager._async_analyzer is None
        assert compat_manager._async_generator is None
        assert compat_manager._async_template_manager is None


class TestAsyncToSyncDecorator:
    """Test async-to-sync decorator functionality."""

    def test_async_to_sync_decorator_success(self):
        """Test decorator with successful async function."""

        @async_to_sync
        async def async_function(x, y):
            await asyncio.sleep(0.001)
            return x + y

        # Should be able to call as sync function
        result = async_function(5, 3)
        assert result == 8

    def test_async_to_sync_decorator_with_kwargs(self):
        """Test decorator with keyword arguments."""

        @async_to_sync
        async def async_function_with_kwargs(a, b=10, c=None):
            await asyncio.sleep(0.001)
            return a + b + (c or 0)

        result = async_function_with_kwargs(5, b=15, c=20)
        assert result == 40

    def test_async_to_sync_decorator_exception(self):
        """Test decorator with function that raises exception."""

        @async_to_sync
        async def failing_async_function():
            await asyncio.sleep(0.001)
            raise RuntimeError("Async function failed")

        with pytest.raises(RuntimeError, match="Async function failed"):
            failing_async_function()


class TestSyncProjectAnalyzerCompat:
    """Test sync wrapper for async project analyzer."""

    @pytest.fixture
    def sync_analyzer(self):
        """Create sync analyzer wrapper for testing."""
        return SyncProjectAnalyzerCompat()

    def test_analyzer_initialization(self, sync_analyzer):
        """Test analyzer initialization."""
        assert sync_analyzer._async_analyzer is not None
        assert sync_analyzer.config is None

    def test_analyzer_with_config(self):
        """Test analyzer initialization with config."""
        config = {"test_setting": "test_value"}
        analyzer = SyncProjectAnalyzerCompat(config)
        assert analyzer.config == config

    @patch("claude_builder.core.async_analyzer.AsyncProjectAnalyzer.analyze_async")
    def test_analyze_sync_wrapper(self, mock_analyze, sync_analyzer):
        """Test sync wrapper for analyze method."""
        # Mock the async analyze method
        mock_analysis = MagicMock(spec=ProjectAnalysis)
        mock_analysis.project_name = "test_project"
        mock_analysis.project_type = ProjectType.LIBRARY

        async def mock_async_analyze(path):
            return mock_analysis

        mock_analyze.side_effect = mock_async_analyze

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = sync_analyzer.analyze(tmp_dir)

        assert result == mock_analysis
        mock_analyze.assert_called_once()

    @patch(
        "claude_builder.core.async_analyzer.AsyncProjectAnalyzer.batch_analyze_async"
    )
    def test_batch_analyze_sync_wrapper(self, mock_batch_analyze, sync_analyzer):
        """Test sync wrapper for batch analyze method."""
        # Mock the async batch analyze method
        mock_analyses = [MagicMock(spec=ProjectAnalysis) for _ in range(3)]

        async def mock_async_batch_analyze(paths):
            return mock_analyses

        mock_batch_analyze.side_effect = mock_async_batch_analyze

        with tempfile.TemporaryDirectory() as tmp_dir:
            paths = [Path(tmp_dir) / f"project_{i}" for i in range(3)]
            for path in paths:
                path.mkdir()

            results = sync_analyzer.batch_analyze(paths)

        assert len(results) == 3
        assert results == mock_analyses
        mock_batch_analyze.assert_called_once()

    def test_get_performance_stats(self, sync_analyzer):
        """Test getting performance statistics."""
        stats = sync_analyzer.get_performance_stats()
        assert isinstance(stats, dict)
        # Stats should come from the underlying async analyzer


class TestSyncTemplateManagerCompat:
    """Test sync wrapper for async template manager."""

    @pytest.fixture
    def sync_template_manager(self):
        """Create sync template manager wrapper for testing."""
        return SyncTemplateManagerCompat()

    def test_template_manager_initialization(self, sync_template_manager):
        """Test template manager initialization."""
        assert sync_template_manager._async_template_manager is not None
        assert sync_template_manager.config is None

    @patch(
        "claude_builder.core.async_template_manager.AsyncTemplateManager.get_template_async"
    )
    def test_get_template_sync_wrapper(self, mock_get_template, sync_template_manager):
        """Test sync wrapper for get template method."""
        mock_template = {"name": "test_template", "content": "test content"}

        async def mock_async_get_template(name, analysis=None):
            return mock_template

        mock_get_template.side_effect = mock_async_get_template

        result = sync_template_manager.get_template("test_template")

        assert result == mock_template
        mock_get_template.assert_called_once_with("test_template", None)

    @patch(
        "claude_builder.core.async_template_manager.AsyncTemplateManager.list_templates_async"
    )
    def test_list_templates_sync_wrapper(
        self, mock_list_templates, sync_template_manager
    ):
        """Test sync wrapper for list templates method."""
        mock_templates = [
            {"name": "template1", "type": "builtin"},
            {"name": "template2", "type": "community"},
        ]

        async def mock_async_list_templates(include_remote=True):
            return mock_templates

        mock_list_templates.side_effect = mock_async_list_templates

        results = sync_template_manager.list_templates(include_remote=False)

        assert results == mock_templates
        mock_list_templates.assert_called_once_with(False)

    @patch(
        "claude_builder.core.async_template_manager.AsyncTemplateManager.search_templates_async"
    )
    def test_search_templates_sync_wrapper(
        self, mock_search_templates, sync_template_manager
    ):
        """Test sync wrapper for search templates method."""
        mock_results = [
            {"name": "python-web", "description": "Python web template"},
        ]

        async def mock_async_search_templates(query, limit=20):
            return mock_results

        mock_search_templates.side_effect = mock_async_search_templates

        results = sync_template_manager.search_templates("python", limit=10)

        assert results == mock_results
        mock_search_templates.assert_called_once_with("python", 10)

    def test_get_performance_stats(self, sync_template_manager):
        """Test getting performance statistics."""
        stats = sync_template_manager.get_performance_stats()
        assert isinstance(stats, dict)


class TestPerformanceBenchmarker:
    """Test performance benchmarking functionality."""

    @pytest.fixture
    def benchmarker(self):
        """Create benchmarker for testing."""
        return PerformanceBenchmarker()

    def test_benchmark_operation_success(self, benchmarker):
        """Test benchmarking successful operations."""

        def sync_func(x):
            import time

            time.sleep(0.01)
            return x * 2

        async def async_func(x):
            await asyncio.sleep(0.01)
            return x * 2

        result = benchmarker.benchmark_operation(
            "multiply_operation", async_func, sync_func, 5
        )

        assert result["operation"] == "multiply_operation"
        assert result["args_count"] == 1
        assert "sync" in result
        assert "async" in result
        assert result["sync"]["success"] is True
        assert result["async"]["success"] is True
        assert "duration" in result["sync"]
        assert "duration" in result["async"]

    def test_benchmark_operation_with_errors(self, benchmarker):
        """Test benchmarking operations with errors."""

        def sync_func_error():
            raise ValueError("Sync error")

        async def async_func_success():
            return "async success"

        result = benchmarker.benchmark_operation(
            "mixed_operation", async_func_success, sync_func_error
        )

        assert result["sync"]["success"] is False
        assert "error" in result["sync"]
        assert result["async"]["success"] is True
        assert "performance_improvement_percent" not in result  # No comparison possible

    def test_benchmark_operation_performance_calculation(self, benchmarker):
        """Test performance improvement calculation."""

        def slow_sync_func():
            import time

            time.sleep(0.02)  # 20ms
            return "sync result"

        async def fast_async_func():
            await asyncio.sleep(0.005)  # 5ms
            return "async result"

        result = benchmarker.benchmark_operation(
            "performance_test", fast_async_func, slow_sync_func
        )

        if "performance_improvement_percent" in result:
            # Async should be faster, so improvement should be positive
            assert result["performance_improvement_percent"] > 0
            assert result["speedup_factor"] > 1

    def test_get_benchmark_summary_empty(self, benchmarker):
        """Test getting benchmark summary when no benchmarks run."""
        summary = benchmarker.get_benchmark_summary()
        assert "message" in summary
        assert "No benchmarks run" in summary["message"]

    def test_get_benchmark_summary_with_data(self, benchmarker):
        """Test getting benchmark summary with benchmark data."""

        # Run a simple benchmark first
        def sync_func():
            return "result"

        async def async_func():
            return "result"

        benchmarker.benchmark_operation("test_op", async_func, sync_func)

        summary = benchmarker.get_benchmark_summary()

        assert "total_benchmarks" in summary
        assert summary["total_benchmarks"] >= 1
        assert "operations" in summary
        assert "test_op" in summary["operations"]

    @patch("claude_builder.core.analyzer.ProjectAnalyzer")
    @patch("claude_builder.core.template_manager.CoreTemplateManager")
    def test_run_comprehensive_benchmarks(
        self, mock_template_manager, mock_analyzer, benchmarker
    ):
        """Test running comprehensive benchmarks."""
        # Mock the sync components
        mock_analyzer_instance = MagicMock()
        mock_analyzer_instance.analyze.return_value = MagicMock(spec=ProjectAnalysis)
        mock_analyzer.return_value = mock_analyzer_instance

        mock_template_manager_instance = MagicMock()
        mock_template_manager_instance.get_template.return_value = {"name": "basic"}
        mock_template_manager.return_value = mock_template_manager_instance

        with tempfile.TemporaryDirectory() as tmp_dir:
            summary = benchmarker.run_comprehensive_benchmarks(tmp_dir)

        assert isinstance(summary, dict)
        # Should have run multiple benchmarks
        assert "total_benchmarks" in summary


class TestGlobalCompatibilityFunctions:
    """Test global compatibility functions."""

    def test_cleanup_compatibility_layer(self):
        """Test global cleanup function."""
        # Should not raise exceptions
        cleanup_compatibility_layer()

    def test_get_performance_overview(self):
        """Test getting global performance overview."""
        overview = get_performance_overview()

        assert isinstance(overview, dict)
        assert "global_performance_monitor" in overview
        assert "benchmark_summary" in overview
        # Other stats may be None if components not initialized

    def test_global_performance_benchmarker(self):
        """Test global performance benchmarker instance."""
        assert performance_benchmarker is not None
        assert isinstance(performance_benchmarker, PerformanceBenchmarker)


class TestIntegrationCompatibility:
    """Integration tests for compatibility layer."""

    def test_sync_analyzer_integration(self):
        """Test sync analyzer integration with real directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a simple Python project structure
            project_dir = Path(tmp_dir) / "test_project"
            project_dir.mkdir()

            # Create basic Python files
            (project_dir / "main.py").write_text("print('Hello, world!')")
            (project_dir / "requirements.txt").write_text("requests>=2.28.0")

            # Test with mocked async analyzer to avoid full implementation
            with patch(
                "claude_builder.core.async_analyzer.AsyncProjectAnalyzer"
            ) as mock_class:
                mock_instance = AsyncMock()
                mock_analysis = MagicMock(spec=ProjectAnalysis)
                mock_analysis.project_name = "test_project"
                mock_analysis.project_type = ProjectType.LIBRARY

                async def mock_analyze_async(path):
                    return mock_analysis

                mock_instance.analyze_async = mock_analyze_async
                mock_instance.get_performance_stats.return_value = {"test": "stats"}
                mock_class.return_value = mock_instance

                analyzer = SyncProjectAnalyzerCompat()
                result = analyzer.analyze(project_dir)

                assert result == mock_analysis
                assert result.project_name == "test_project"

    def test_error_propagation_through_compatibility_layer(self):
        """Test that errors propagate correctly through compatibility layer."""
        with patch(
            "claude_builder.core.async_analyzer.AsyncProjectAnalyzer"
        ) as mock_class:
            mock_instance = AsyncMock()

            async def mock_analyze_async_error(path):
                raise PerformanceError("Analysis failed")

            mock_instance.analyze_async = mock_analyze_async_error
            mock_class.return_value = mock_instance

            analyzer = SyncProjectAnalyzerCompat()

            with pytest.raises(PerformanceError, match="Analysis failed"):
                analyzer.analyze("/nonexistent/path")

    def test_compatibility_with_concurrent_operations(self):
        """Test compatibility layer with concurrent sync operations."""
        import threading

        results = {}
        errors = {}

        def run_analysis(thread_id):
            try:
                with patch(
                    "claude_builder.core.async_analyzer.AsyncProjectAnalyzer"
                ) as mock_class:
                    mock_instance = AsyncMock()
                    mock_analysis = MagicMock(spec=ProjectAnalysis)
                    mock_analysis.project_name = f"project_{thread_id}"

                    async def mock_analyze_async(path):
                        await asyncio.sleep(0.01)  # Simulate work
                        return mock_analysis

                    mock_instance.analyze_async = mock_analyze_async
                    mock_instance.get_performance_stats.return_value = {}
                    mock_class.return_value = mock_instance

                    analyzer = SyncProjectAnalyzerCompat()
                    result = analyzer.analyze(f"/tmp/project_{thread_id}")
                    results[thread_id] = result

            except Exception as e:
                errors[thread_id] = e

        # Run multiple threads concurrently
        threads = []
        for i in range(3):
            thread = threading.Thread(target=run_analysis, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(timeout=5)

        # All operations should succeed
        assert len(results) == 3
        assert len(errors) == 0

        for i in range(3):
            assert results[i].project_name == f"project_{i}"
