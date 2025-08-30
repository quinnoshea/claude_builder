"""Async template manager for Claude Builder.

This module provides the main async interface for template management,
integrating all async components for optimal performance in Phase 3.4.
"""

import asyncio

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from claude_builder.core.models import ProjectAnalysis, ValidationResult
from claude_builder.core.template_management.community.template_repository import (
    CommunityTemplate,
    CommunityTemplateManager,
)
from claude_builder.core.template_management.network.async_template_downloader import (
    AsyncTemplateDownloader,
    AsyncTemplateRepositoryClient,
)
from claude_builder.core.template_management.validation.template_validator import (
    ComprehensiveTemplateValidator,
)
from claude_builder.utils.async_performance import cache, performance_monitor
from claude_builder.utils.exceptions import PerformanceError, TemplateError


class AsyncTemplateManager:
    """Async template manager with comprehensive performance optimization."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        *,
        max_concurrent_operations: int = 10,
        enable_caching: bool = True,
        template_cache_ttl: int = 3600,  # 1 hour
    ):
        """Initialize async template manager.

        Args:
            config: Template manager configuration
            max_concurrent_operations: Maximum concurrent template operations
            enable_caching: Whether to enable template caching
            template_cache_ttl: Template cache TTL in seconds
        """
        self.config = config or {}
        self.max_concurrent_operations = max_concurrent_operations
        self.enable_caching = enable_caching
        self.template_cache_ttl = template_cache_ttl

        # Core components
        self.downloader = AsyncTemplateDownloader(
            max_concurrent_downloads=max_concurrent_operations,
            enable_caching=enable_caching,
        )
        self.validator = ComprehensiveTemplateValidator()
        self.community_manager = CommunityTemplateManager()

        # Repository clients
        self._repository_clients: Dict[str, AsyncTemplateRepositoryClient] = {}

        # Performance management
        self._semaphore = asyncio.Semaphore(max_concurrent_operations)
        self._template_locks: Dict[str, asyncio.Lock] = {}

    async def get_template_async(
        self, template_name: str, analysis: Optional[ProjectAnalysis] = None
    ) -> Optional[Dict[str, Any]]:
        """Get template asynchronously with intelligent caching.

        Args:
            template_name: Name of the template to retrieve
            analysis: Optional project analysis for template customization

        Returns:
            Template data or None if not found
        """
        async with performance_monitor.track_operation("get_template_async") as op:
            op["template_name"] = template_name

            # Check cache first
            cache_key = f"template:{template_name}"
            if analysis:
                cache_key += f":{hash(str(analysis))}"

            if self.enable_caching:
                cached_template = await cache.get(cache_key)
                if cached_template is not None:
                    op["cache_hit"] = True
                    return cached_template

            async with self._semaphore:
                # Use lock for specific template to avoid duplicate downloads
                template_lock = self._get_template_lock(template_name)
                async with template_lock:
                    # Double-check cache after acquiring lock
                    if self.enable_caching:
                        cached_template = await cache.get(cache_key)
                        if cached_template is not None:
                            return cached_template

                    # Load template from various sources
                    template = await self._load_template_from_sources(
                        template_name, analysis
                    )

                    if template and self.enable_caching:
                        await cache.set(cache_key, template)

                    return template

    async def _load_template_from_sources(
        self, template_name: str, analysis: Optional[ProjectAnalysis] = None
    ) -> Optional[Dict[str, Any]]:
        """Load template from multiple sources concurrently."""
        # Define template loading strategies
        loading_strategies = [
            self._load_builtin_template,
            self._load_community_template,
            self._load_remote_template,
        ]

        # Try strategies concurrently
        tasks = []
        for strategy in loading_strategies:
            task = asyncio.create_task(
                self._try_loading_strategy(strategy, template_name, analysis)
            )
            tasks.append(task)

        # Wait for first successful result
        for completed_task in asyncio.as_completed(tasks):
            try:
                result = await completed_task
                if result is not None:
                    # Cancel remaining tasks
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    return result
            except Exception:
                # Continue with other strategies
                continue

        return None

    async def _try_loading_strategy(
        self,
        strategy_func,
        template_name: str,
        analysis: Optional[ProjectAnalysis] = None,
    ) -> Optional[Dict[str, Any]]:
        """Try a template loading strategy with error handling."""
        try:
            return await strategy_func(template_name, analysis)
        except Exception:
            # Strategy failed, return None
            return None

    async def _load_builtin_template(
        self, template_name: str, analysis: Optional[ProjectAnalysis] = None
    ) -> Optional[Dict[str, Any]]:
        """Load builtin template asynchronously."""
        # Run builtin template loading in executor
        return await asyncio.get_event_loop().run_in_executor(
            None, self._load_builtin_template_sync, template_name, analysis
        )

    def _load_builtin_template_sync(
        self, template_name: str, analysis: Optional[ProjectAnalysis] = None
    ) -> Optional[Dict[str, Any]]:
        """Synchronous builtin template loading."""
        # This would interface with the builtin template system
        builtin_templates = {
            "basic": {
                "name": "basic",
                "type": "builtin",
                "content": "# Basic template\nProject: $project_name",
                "variables": ["project_name"],
            },
            "python": {
                "name": "python",
                "type": "builtin",
                "content": "# Python Project\nLanguages: Python\nFrameworks: $frameworks",
                "variables": ["frameworks"],
            },
        }

        return builtin_templates.get(template_name)

    async def _load_community_template(
        self, template_name: str, analysis: Optional[ProjectAnalysis] = None
    ) -> Optional[Dict[str, Any]]:
        """Load community template asynchronously."""
        try:
            # Get community template metadata
            community_templates = await asyncio.get_event_loop().run_in_executor(
                None, self.community_manager.list_templates
            )

            for template in community_templates:
                if template.name == template_name:
                    # Download template if needed
                    template_path = await self._download_community_template(template)
                    return await self._load_template_from_path(template_path)

            return None

        except Exception:
            return None

    async def _load_remote_template(
        self, template_name: str, analysis: Optional[ProjectAnalysis] = None
    ) -> Optional[Dict[str, Any]]:
        """Load template from remote repositories."""
        try:
            # Try default repositories
            repository_urls = self.config.get(
                "template_repositories",
                [
                    "https://github.com/claude-builder/templates",
                    "https://cdn.claude-builder.dev/templates",
                ],
            )

            for repo_url in repository_urls:
                client = await self._get_repository_client(repo_url)
                try:
                    metadata = await client.get_template_metadata_async(template_name)
                    if metadata:
                        # Download and return template
                        return await self._download_remote_template(
                            client, template_name
                        )
                except Exception:
                    continue

            return None

        except Exception:
            return None

    async def validate_template_async(
        self, template_path: Union[str, Path]
    ) -> ValidationResult:
        """Validate template asynchronously.

        Args:
            template_path: Path to template file or directory

        Returns:
            Validation result with performance metrics
        """
        async with performance_monitor.track_operation("validate_template_async") as op:
            op["template_path"] = str(template_path)

            try:
                # Run validation in executor to avoid blocking
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self.validator.validate_template, template_path
                )

                op["validation_result"] = result.is_valid
                op["error_count"] = len(result.errors)

                return result

            except Exception as e:
                raise PerformanceError(f"Template validation failed: {e}") from e

    async def install_template_async(
        self, template_source: str, destination: Optional[Path] = None
    ) -> Path:
        """Install template asynchronously from various sources.

        Args:
            template_source: URL, path, or template name
            destination: Optional destination directory

        Returns:
            Path to installed template
        """
        async with performance_monitor.track_operation("install_template_async") as op:
            op["template_source"] = template_source

            async with self._semaphore:
                try:
                    if template_source.startswith(("http://", "https://")):
                        # Remote template
                        return await self._install_remote_template(
                            template_source, destination
                        )
                    if Path(template_source).exists():
                        # Local template
                        return await self._install_local_template(
                            template_source, destination
                        )
                    # Template name - try repositories
                    return await self._install_named_template(
                        template_source, destination
                    )

                except Exception as e:
                    raise TemplateError(f"Template installation failed: {e}") from e

    async def _install_remote_template(
        self, template_url: str, destination: Optional[Path]
    ) -> Path:
        """Install template from remote URL."""
        if destination is None:
            destination = Path.cwd() / "templates" / "downloaded"

        destination.mkdir(parents=True, exist_ok=True)

        # Download template bundle
        await self.downloader.download_template_bundle_async(template_url, destination)

        return destination

    async def _install_local_template(
        self, template_path: str, destination: Optional[Path]
    ) -> Path:
        """Install template from local path."""
        source_path = Path(template_path)

        if destination is None:
            destination = Path.cwd() / "templates" / source_path.name

        # Copy template files asynchronously
        await self._copy_template_files(source_path, destination)

        return destination

    async def _install_named_template(
        self, template_name: str, destination: Optional[Path]
    ) -> Path:
        """Install template by name from repositories."""
        template = await self.get_template_async(template_name)

        if not template:
            raise TemplateError(f"Template not found: {template_name}")

        if destination is None:
            destination = Path.cwd() / "templates" / template_name

        # Install based on template type
        if template.get("type") == "remote":
            return await self._install_remote_template(
                template["source_url"], destination
            )
        # Save builtin template
        await self._save_template_content(template, destination)
        return destination

    async def list_templates_async(
        self, include_remote: bool = True
    ) -> List[Dict[str, Any]]:
        """List available templates asynchronously.

        Args:
            include_remote: Whether to include remote repository templates

        Returns:
            List of template metadata
        """
        async with performance_monitor.track_operation("list_templates_async"):
            template_lists = []

            # Get builtin templates
            builtin_task = asyncio.create_task(
                asyncio.get_event_loop().run_in_executor(
                    None, self._list_builtin_templates
                )
            )
            template_lists.append(builtin_task)

            # Get community templates
            community_task = asyncio.create_task(
                asyncio.get_event_loop().run_in_executor(
                    None, self.community_manager.list_templates
                )
            )
            template_lists.append(community_task)

            # Get remote templates if requested
            if include_remote:
                for repo_url in self.config.get("template_repositories", []):
                    client = await self._get_repository_client(repo_url)
                    remote_task = asyncio.create_task(client.list_templates_async())
                    template_lists.append(remote_task)

            # Wait for all lists
            results = await asyncio.gather(*template_lists, return_exceptions=True)

            # Combine results
            all_templates = []
            for result in results:
                if isinstance(result, list):
                    all_templates.extend(result)

            return all_templates

    async def search_templates_async(
        self, query: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search templates asynchronously across all sources.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching templates
        """
        async with performance_monitor.track_operation("search_templates_async") as op:
            op["query"] = query
            op["limit"] = limit

            # Search across all sources concurrently
            search_tasks = []

            # Search remote repositories
            for repo_url in self.config.get("template_repositories", []):
                client = await self._get_repository_client(repo_url)
                task = asyncio.create_task(client.search_templates_async(query, limit))
                search_tasks.append(task)

            # Wait for search results
            results = await asyncio.gather(*search_tasks, return_exceptions=True)

            # Combine and deduplicate results
            found_templates = []
            seen_names = set()

            for result in results:
                if isinstance(result, list):
                    for template in result:
                        name = template.get("name")
                        if name and name not in seen_names:
                            found_templates.append(template)
                            seen_names.add(name)

                            if len(found_templates) >= limit:
                                break

                if len(found_templates) >= limit:
                    break

            return found_templates[:limit]

    # Helper methods
    def _get_template_lock(self, template_name: str) -> asyncio.Lock:
        """Get or create lock for specific template."""
        if template_name not in self._template_locks:
            self._template_locks[template_name] = asyncio.Lock()
        return self._template_locks[template_name]

    async def _get_repository_client(
        self, repo_url: str
    ) -> AsyncTemplateRepositoryClient:
        """Get or create repository client for URL."""
        if repo_url not in self._repository_clients:
            self._repository_clients[repo_url] = AsyncTemplateRepositoryClient(
                repo_url, downloader=self.downloader
            )
        return self._repository_clients[repo_url]

    async def _download_community_template(self, template: CommunityTemplate) -> Path:
        """Download community template."""
        # This would implement community template download logic
        # For now, return a placeholder path
        return Path("/tmp/community_template")

    async def _load_template_from_path(
        self, template_path: Path
    ) -> Optional[Dict[str, Any]]:
        """Load template from local path."""
        # This would implement template loading from path
        return {
            "name": template_path.name,
            "type": "local",
            "path": str(template_path),
        }

    async def _download_remote_template(
        self, client: AsyncTemplateRepositoryClient, template_name: str
    ) -> Optional[Dict[str, Any]]:
        """Download template from remote repository."""
        try:
            metadata = await client.get_template_metadata_async(template_name)
            return {
                "name": template_name,
                "type": "remote",
                "metadata": metadata,
            }
        except Exception:
            return None

    async def _copy_template_files(self, source: Path, destination: Path) -> None:
        """Copy template files asynchronously."""
        # This would implement async file copying
        destination.mkdir(parents=True, exist_ok=True)
        # For now, just create destination directory

    async def _save_template_content(
        self, template: Dict[str, Any], destination: Path
    ) -> None:
        """Save template content to destination."""
        destination.mkdir(parents=True, exist_ok=True)
        template_file = destination / "template.md"

        async with performance_monitor.track_operation("save_template_content"):
            content = template.get("content", "# Empty template")

            import aiofiles

            async with aiofiles.open(template_file, "w", encoding="utf-8") as f:
                await f.write(content)

    def _list_builtin_templates(self) -> List[Dict[str, Any]]:
        """List builtin templates (synchronous)."""
        return [
            {"name": "basic", "type": "builtin", "description": "Basic template"},
            {
                "name": "python",
                "type": "builtin",
                "description": "Python project template",
            },
            {
                "name": "web",
                "type": "builtin",
                "description": "Web application template",
            },
        ]

    async def batch_process_templates_async(
        self, template_operations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process multiple template operations concurrently.

        Args:
            template_operations: List of operations like:
                [
                    {"operation": "get", "template_name": "python"},
                    {"operation": "install", "source": "https://..."},
                    {"operation": "validate", "path": "/path/to/template"},
                ]

        Returns:
            List of operation results
        """
        async with performance_monitor.track_operation(
            "batch_template_operations"
        ) as op:
            op["operation_count"] = len(template_operations)

            # Create operation tasks
            tasks = []
            for i, operation in enumerate(template_operations):
                task = asyncio.create_task(
                    self._execute_template_operation(i, operation),
                    name=f"template_op_{i}",
                )
                tasks.append(task)

            # Wait for all operations
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    processed_results.append(
                        {
                            "success": False,
                            "error": str(result),
                            "error_type": type(result).__name__,
                        }
                    )
                else:
                    processed_results.append(result)

            return processed_results

    async def _execute_template_operation(
        self, index: int, operation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single template operation."""
        try:
            op_type = operation.get("operation")

            if op_type == "get":
                template = await self.get_template_async(operation["template_name"])
                return {
                    "index": index,
                    "success": True,
                    "operation": "get",
                    "result": template,
                }

            if op_type == "install":
                path = await self.install_template_async(operation["source"])
                return {
                    "index": index,
                    "success": True,
                    "operation": "install",
                    "result": str(path),
                }

            if op_type == "validate":
                validation_result = await self.validate_template_async(
                    operation["path"]
                )
                return {
                    "index": index,
                    "success": True,
                    "operation": "validate",
                    "result": validation_result,
                }

            return {
                "index": index,
                "success": False,
                "error": f"Unknown operation: {op_type}",
            }

        except Exception as e:
            return {
                "index": index,
                "success": False,
                "operation": operation.get("operation"),
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        return {
            "template_manager_config": {
                "max_concurrent_operations": self.max_concurrent_operations,
                "caching_enabled": self.enable_caching,
                "cache_ttl": self.template_cache_ttl,
            },
            "active_operations": self._semaphore.locked(),
            "available_slots": self._semaphore._value,
            "template_locks": len(self._template_locks),
            "repository_clients": len(self._repository_clients),
            "cache_stats": cache.get_stats(),
            "operation_metrics": performance_monitor.get_metrics(),
            "downloader_stats": self.downloader.get_performance_stats(),
        }

    async def cleanup_async(self) -> None:
        """Clean up async resources."""
        # Close repository clients if they have cleanup methods
        cleanup_tasks = []

        for client in self._repository_clients.values():
            if hasattr(client, "cleanup"):
                task = asyncio.create_task(client.cleanup())
                cleanup_tasks.append(task)

        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        # Clear caches and locks
        self._repository_clients.clear()
        self._template_locks.clear()
