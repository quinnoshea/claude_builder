"""Async performance optimization framework for Claude Builder.

This module provides comprehensive async patterns, memory optimization,
and performance monitoring capabilities for the Phase 3.4 implementation.
"""

import asyncio
import functools
import gc
import logging
import time

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, AsyncIterable, Callable, Dict, Optional, TypeVar
from weakref import WeakSet

import aiofiles
import aiohttp
import psutil

from claude_builder.utils.exceptions import PerformanceError


# Type variables for generic async patterns
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class OperationContext:
    """Context object for tracking async operations.

    This class is used instead of dictionaries to allow weak references.
    """

    def __init__(self, name: str, start_time: float, start_memory: int):
        self.name = name
        self.start_time = start_time
        self.start_memory = start_memory
        self.metadata: Dict[str, Any] = {}

    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dict-like access for backward compatibility."""
        self.metadata[key] = value

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access for backward compatibility."""
        if key == "name":
            return self.name
        if key == "start_time":
            return self.start_time
        if key == "start_memory":
            return self.start_memory
        return self.metadata[key]

    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return key in ["name", "start_time", "start_memory"] or key in self.metadata


class AsyncPerformanceMonitor:
    """Comprehensive performance monitoring for async operations."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._active_operations: WeakSet = WeakSet()
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self._memory_threshold = 0.85  # 85% memory usage threshold
        self._cpu_threshold = 0.90  # 90% CPU usage threshold

    def register_operation(self, operation_name: str) -> None:
        """Register an async operation for monitoring."""
        if operation_name not in self._metrics:
            self._metrics[operation_name] = {
                "count": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
                "memory_peak": 0,
                "errors": 0,
            }

    @asynccontextmanager
    async def track_operation(
        self, operation_name: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Context manager for tracking async operation performance."""
        self.register_operation(operation_name)

        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss

        operation_context = OperationContext(
            name=operation_name,
            start_time=start_time,
            start_memory=start_memory,
        )

        self._active_operations.add(operation_context)

        try:
            yield operation_context
        except Exception as e:
            self._metrics[operation_name]["errors"] += 1
            self.logger.error(f"Operation {operation_name} failed: {e}")
            raise
        finally:
            end_time = time.perf_counter()
            end_memory = psutil.Process().memory_info().rss

            duration = end_time - start_time
            memory_used = max(0, end_memory - start_memory)

            # Update metrics
            metrics = self._metrics[operation_name]
            metrics["count"] += 1
            metrics["total_time"] += duration
            metrics["avg_time"] = metrics["total_time"] / metrics["count"]
            metrics["min_time"] = min(metrics["min_time"], duration)
            metrics["max_time"] = max(metrics["max_time"], duration)
            metrics["memory_peak"] = max(metrics["memory_peak"], memory_used)

            # Check performance thresholds
            await self._check_performance_thresholds(
                operation_name, duration, memory_used
            )

            self._active_operations.discard(operation_context)

    async def _check_performance_thresholds(
        self, operation_name: str, duration: float, memory_used: int
    ) -> None:
        """Check if operation exceeds performance thresholds."""
        # Check memory usage
        memory_percent = psutil.virtual_memory().percent / 100.0
        if memory_percent > self._memory_threshold:
            self.logger.warning(
                f"High memory usage during {operation_name}: {memory_percent:.1%}"
            )
            await self._trigger_garbage_collection()

        # Check CPU usage
        cpu_percent = psutil.cpu_percent() / 100.0
        if cpu_percent > self._cpu_threshold:
            self.logger.warning(
                f"High CPU usage during {operation_name}: {cpu_percent:.1%}"
            )

    async def _trigger_garbage_collection(self) -> None:
        """Trigger garbage collection to free memory."""
        self.logger.info("Triggering garbage collection for memory optimization")
        gc.collect()
        await asyncio.sleep(0)  # Yield control

    def get_metrics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics for operations."""
        if operation_name:
            return self._metrics.get(operation_name, {})
        return self._metrics.copy()

    def get_active_operations_count(self) -> int:
        """Get count of currently active operations."""
        return len(self._active_operations)


class AsyncConnectionPool:
    """Connection pool manager for HTTP operations."""

    def __init__(
        self,
        *,
        max_connections: int = 10,
        timeout: int = 30,
        keepalive_timeout: int = 60,
    ):
        self.max_connections = max_connections
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.keepalive_timeout = keepalive_timeout
        self._session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self) -> aiohttp.ClientSession:
        """Create and return HTTP session."""
        connector = aiohttp.TCPConnector(
            limit=self.max_connections,
            keepalive_timeout=self.keepalive_timeout,
            enable_cleanup_closed=True,
        )

        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers={"User-Agent": "Claude-Builder/0.1.0"},
        )

        self.logger.debug(
            f"Created HTTP session with {self.max_connections} max connections"
        )
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
            self.logger.debug("Closed HTTP session")


class AsyncFileProcessor:
    """Async file processing with memory optimization."""

    def __init__(self, *, chunk_size: int = 8192, max_concurrent_files: int = 5):
        self.chunk_size = chunk_size
        self.max_concurrent_files = max_concurrent_files
        self._semaphore = asyncio.Semaphore(max_concurrent_files)
        self.logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def process_file(
        self, file_path: Path
    ) -> AsyncGenerator[aiofiles.threadpool.text.AsyncTextIOWrapper, None]:
        """Process file with memory-efficient streaming."""
        async with self._semaphore:
            try:
                async with aiofiles.open(file_path, encoding="utf-8") as f:
                    yield f
            except Exception as e:
                self.logger.error(f"Error processing file {file_path}: {e}")
                raise PerformanceError(f"File processing failed: {e}") from e

    async def read_file_chunks(self, file_path: Path) -> AsyncGenerator[str, None]:
        """Read file in chunks for memory efficiency."""
        async with self.process_file(file_path) as f:
            while True:
                chunk = await f.read(self.chunk_size)
                if not chunk:
                    break
                yield chunk

    async def write_file_stream(
        self, file_path: Path, content_stream: AsyncIterable[str]
    ) -> None:
        """Write file from async stream with memory optimization."""
        async with self._semaphore:
            try:
                async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                    async for chunk in content_stream:
                        await f.write(chunk)
                        # Yield control periodically for other operations
                        await asyncio.sleep(0)
            except Exception as e:
                self.logger.error(f"Error writing file {file_path}: {e}")
                raise PerformanceError(f"File writing failed: {e}") from e


class AsyncCache:
    """High-performance async LRU cache with TTL."""

    def __init__(self, *, max_size: int = 128, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self.logger = logging.getLogger(__name__)

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value with TTL check."""
        if key not in self._cache:
            return None

        cache_entry = self._cache[key]
        current_time = time.time()

        # Check TTL expiration
        if current_time - cache_entry["timestamp"] > self.ttl_seconds:
            await self._evict(key)
            return None

        # Update access time for LRU
        self._access_times[key] = current_time
        return cache_entry["value"]

    async def set(self, key: str, value: Any) -> None:
        """Set cached value with automatic eviction."""
        current_time = time.time()

        # Evict if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            await self._evict_lru()

        self._cache[key] = {
            "value": value,
            "timestamp": current_time,
        }
        self._access_times[key] = current_time

    async def _evict(self, key: str) -> None:
        """Evict specific cache entry."""
        self._cache.pop(key, None)
        self._access_times.pop(key, None)

    async def _evict_lru(self) -> None:
        """Evict least recently used cache entry."""
        if not self._access_times:
            return

        lru_key = min(self._access_times.keys(), key=self._access_times.get)
        await self._evict(lru_key)
        self.logger.debug(f"Evicted LRU cache entry: {lru_key}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_ratio": len(self._cache) / max(1, len(self._access_times)),
            "ttl_seconds": self.ttl_seconds,
        }


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable[[F], F]:
    """Decorator for async operations with exponential backoff retry."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        raise

                    wait_time = delay * (backoff_factor**attempt)
                    logging.getLogger(__name__).warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                        f"Retrying in {wait_time:.1f}s"
                    )
                    await asyncio.sleep(wait_time)

            raise last_exception  # This should never be reached

        return wrapper

    return decorator


def async_rate_limit(
    calls_per_second: float = 5.0,
    burst_size: int = 10,
) -> Callable[[F], F]:
    """Decorator for rate limiting async operations."""
    # Token bucket algorithm implementation
    tokens = burst_size
    last_update = time.time()

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal tokens, last_update

            now = time.time()
            # Add tokens based on elapsed time
            tokens = min(burst_size, tokens + (now - last_update) * calls_per_second)
            last_update = now

            if tokens < 1:
                # Calculate wait time for next token
                wait_time = (1 - tokens) / calls_per_second
                await asyncio.sleep(wait_time)
                tokens = 0
            else:
                tokens -= 1

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Global instances for shared use
performance_monitor = AsyncPerformanceMonitor()
file_processor = AsyncFileProcessor()
cache = AsyncCache()
