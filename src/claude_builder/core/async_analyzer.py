"""Async project analysis engine for Claude Builder.

This module provides async implementations of project analysis operations,
optimized for performance and concurrent processing in Phase 3.4.
"""

import asyncio
import json

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import aiofiles
import toml

from claude_builder.core.analyzer import (
    ArchitectureDetector,
    ComplexityAssessor,
    DomainDetector,
    FrameworkDetector,
    LanguageDetector,
)
from claude_builder.core.models import (
    ArchitecturePattern,
    DevelopmentEnvironment,
    DomainInfo,
    FileSystemInfo,
    FrameworkInfo,
    LanguageInfo,
    ProjectAnalysis,
    ProjectType,
)
from claude_builder.utils.async_performance import (
    AsyncFileProcessor,
    async_retry,
    cache,
    performance_monitor,
)
from claude_builder.utils.exceptions import AnalysisError, PerformanceError


class AsyncProjectAnalyzer:
    """Async project analyzer with performance optimization."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        *,
        max_concurrent_files: int = 10,
        enable_caching: bool = True,
    ):
        """Initialize async analyzer.

        Args:
            config: Analyzer configuration
            max_concurrent_files: Maximum concurrent file operations
            enable_caching: Whether to enable analysis result caching
        """
        self.config = config or {}
        self.max_concurrent_files = max_concurrent_files
        self.enable_caching = enable_caching

        self.ignore_patterns = self.config.get(
            "ignore_patterns",
            [
                ".git/",
                "node_modules/",
                "__pycache__/",
                "target/",
                "dist/",
                "build/",
                ".venv/",
                "venv/",
                ".tox/",
                ".coverage",
            ],
        )
        self.confidence_threshold = self.config.get("confidence_threshold", 80)

        # Initialize detectors (sync components)
        self.language_detector = LanguageDetector()
        self.framework_detector = FrameworkDetector()
        self.architecture_detector = ArchitectureDetector()
        self.domain_detector = DomainDetector()
        self.complexity_assessor = ComplexityAssessor()

        # Performance components
        self._file_processor = AsyncFileProcessor(
            max_concurrent_files=max_concurrent_files
        )
        self._semaphore = asyncio.Semaphore(max_concurrent_files)

    @async_retry(max_attempts=2, delay=0.5, exceptions=(AnalysisError,))
    async def analyze_async(self, project_path: Union[str, Path]) -> ProjectAnalysis:
        """Analyze project asynchronously with comprehensive optimization.

        Args:
            project_path: Path to project directory

        Returns:
            Complete project analysis
        """
        project_path = Path(project_path).resolve()

        async with performance_monitor.track_operation("async_project_analysis") as op:
            op["project_path"] = str(project_path)

            # Check cache first
            cache_key = (
                f"project_analysis:{project_path}:{project_path.stat().st_mtime}"
            )
            if self.enable_caching:
                cached_result = await cache.get(cache_key)
                if cached_result is not None:
                    return cached_result  # type: ignore[no-any-return]

            try:
                if not project_path.exists():
                    raise AnalysisError(f"Project path does not exist: {project_path}")

                if not project_path.is_dir():
                    raise AnalysisError(
                        f"Project path is not a directory: {project_path}"
                    )

                # Perform concurrent analysis
                analysis_tasks = [
                    self._analyze_filesystem_async(project_path),
                    self._analyze_languages_async(project_path),
                    self._analyze_frameworks_async(project_path),
                    self._analyze_architecture_async(project_path),
                    self._analyze_domain_async(project_path),
                ]

                results = await asyncio.gather(*analysis_tasks)

                filesystem_info = results[0]
                languages = results[1]
                frameworks = results[2]
                architecture = results[3]
                domain_info = results[4]

                # Type assertions for mypy
                assert isinstance(filesystem_info, FileSystemInfo)
                assert isinstance(languages, list)
                assert isinstance(frameworks, list)
                assert isinstance(architecture, ArchitecturePattern)
                assert isinstance(domain_info, DomainInfo)

                # Calculate complexity (CPU-intensive, run in thread)
                # Ensure we have proper objects for complexity assessment
                language_info = languages[0] if languages else LanguageInfo()
                framework_info = frameworks[0] if frameworks else FrameworkInfo()
                dev_env = (
                    DevelopmentEnvironment()
                )  # TODO: Implement proper dev env detection

                complexity = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.complexity_assessor.assess,
                    filesystem_info,
                    language_info,
                    framework_info,
                    dev_env,
                )

                # Determine project type
                project_type = await self._determine_project_type_async(
                    languages, frameworks, filesystem_info
                )

                # Create analysis result using correct constructor parameters
                analysis = ProjectAnalysis(
                    project_path=project_path,
                    language_info=language_info,
                    framework_info=framework_info,
                    domain_info=domain_info,
                    project_type=project_type,
                    complexity_level=complexity,
                    architecture_pattern=architecture,
                    dev_environment=dev_env,
                    filesystem_info=filesystem_info,
                    analysis_confidence=self._calculate_confidence_score(
                        languages, frameworks, architecture, domain_info
                    ),
                    analysis_timestamp=datetime.utcnow().isoformat(),
                    analyzer_version="0.1.0-async",
                )

                # Cache successful result
                if self.enable_caching:
                    await cache.set(cache_key, analysis)

                return analysis

            except Exception as e:
                if isinstance(e, (AnalysisError, PerformanceError)):
                    raise
                raise AnalysisError(f"Project analysis failed: {e}") from e

    async def _analyze_filesystem_async(self, project_path: Path) -> FileSystemInfo:
        """Analyze filesystem structure asynchronously."""
        async with performance_monitor.track_operation("filesystem_analysis"):
            file_counts: Dict[str, int] = defaultdict(int)
            total_size = 0
            directory_count = 0
            file_extensions: Dict[str, int] = defaultdict(int)

            async for file_path in self._walk_directory_async(project_path):
                if file_path.is_dir():
                    directory_count += 1
                    continue

                try:
                    stat_info = await asyncio.get_event_loop().run_in_executor(
                        None, file_path.stat
                    )
                    file_size = stat_info.st_size
                    total_size += file_size

                    extension = file_path.suffix.lower()
                    if extension:
                        file_extensions[extension] += 1

                    # Categorize file types
                    if extension in [".py", ".pyx", ".pyi"]:
                        file_counts["python"] += 1
                    elif extension in [".js", ".jsx", ".ts", ".tsx"]:
                        file_counts["javascript"] += 1
                    elif extension in [".rs"]:
                        file_counts["rust"] += 1
                    elif extension in [".java", ".kt", ".scala"]:
                        file_counts["jvm"] += 1
                    elif extension in [".go"]:
                        file_counts["go"] += 1
                    elif extension in [".c", ".cpp", ".cc", ".h", ".hpp"]:
                        file_counts["c_cpp"] += 1
                    elif extension in [".md", ".rst", ".txt"]:
                        file_counts["documentation"] += 1
                    elif extension in [".json", ".yaml", ".yml", ".toml"]:
                        file_counts["configuration"] += 1
                    else:
                        file_counts["other"] += 1

                except (OSError, PermissionError):
                    # Skip files we can't access
                    continue

            # Use the actual FileSystemInfo structure from models.py
            filesystem_info = FileSystemInfo()
            filesystem_info.total_files = sum(file_counts.values())
            filesystem_info.total_directories = directory_count
            # Note: total_size_bytes is not part of FileSystemInfo model
            # file_type_distribution and file_extensions are not part of base model

            return filesystem_info

    async def _walk_directory_async(self, path: Path) -> AsyncGenerator[Path, None]:
        """Walk directory tree asynchronously with ignore patterns."""
        try:
            async for entry in self._scan_directory_async(path):
                # Check ignore patterns
                relative_path = entry.relative_to(path)
                if any(
                    pattern in str(relative_path) for pattern in self.ignore_patterns
                ):
                    continue

                yield entry

                if entry.is_dir() and entry != path:
                    async for sub_entry in self._walk_directory_async(entry):
                        yield sub_entry
        except (OSError, PermissionError):
            # Skip directories we can't access
            return

    async def _scan_directory_async(self, path: Path) -> AsyncGenerator[Path, None]:
        """Scan directory entries asynchronously."""
        try:
            # Use executor for directory scanning to avoid blocking
            entries = await asyncio.get_event_loop().run_in_executor(
                None, list, path.iterdir()
            )

            for entry in entries:
                yield entry
                # Yield control periodically
                await asyncio.sleep(0)

        except (OSError, PermissionError):
            return

    async def _analyze_languages_async(self, project_path: Path) -> List[LanguageInfo]:
        """Analyze programming languages asynchronously."""
        async with performance_monitor.track_operation("language_analysis"):
            # Run language detection in executor (CPU-intensive)
            # Use existing detect_primary_language method and wrap in list
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.language_detector.detect_primary_language, project_path
            )
            return [result] if result.primary else []

    async def _analyze_frameworks_async(
        self, project_path: Path
    ) -> List[FrameworkInfo]:
        """Analyze frameworks asynchronously."""
        async with performance_monitor.track_operation("framework_analysis"):
            # Look for framework indicators concurrently
            framework_tasks = []

            # Check for specific framework files
            framework_files = {
                "package.json": self._detect_node_frameworks,
                "requirements.txt": self._detect_python_frameworks,
                "pyproject.toml": self._detect_python_frameworks,
                "Cargo.toml": self._detect_rust_frameworks,
                "pom.xml": self._detect_java_frameworks,
                "build.gradle": self._detect_java_frameworks,
                "go.mod": self._detect_go_frameworks,
            }

            for filename, detector in framework_files.items():
                file_path = project_path / filename
                if file_path.exists():
                    task = asyncio.create_task(
                        self._run_framework_detector(detector, file_path)
                    )
                    framework_tasks.append(task)

            # Wait for all framework detection tasks
            if framework_tasks:
                results = await asyncio.gather(*framework_tasks, return_exceptions=True)
                frameworks = []
                for result in results:
                    if isinstance(result, list):
                        frameworks.extend(result)
            else:
                # Fallback to sync detection
                frameworks = await asyncio.get_event_loop().run_in_executor(
                    None, self.framework_detector.detect_frameworks, project_path
                )

            return frameworks

    async def _run_framework_detector(
        self, detector_func: Any, file_path: Path
    ) -> List[FrameworkInfo]:
        """Run framework detector in executor."""
        return await asyncio.get_event_loop().run_in_executor(
            None, detector_func, file_path
        )

    async def _detect_node_frameworks(
        self, package_json_path: Path
    ) -> List[FrameworkInfo]:
        """Detect Node.js frameworks from package.json."""
        try:
            async with aiofiles.open(package_json_path, encoding="utf-8") as f:
                content = await f.read()
                package_data = json.loads(content)

            frameworks = []
            dependencies = {}
            dependencies.update(package_data.get("dependencies", {}))
            dependencies.update(package_data.get("devDependencies", {}))

            # Framework detection logic
            if "react" in dependencies:
                frameworks.append(
                    FrameworkInfo(
                        primary="React",
                        version=dependencies["react"],
                        confidence=0.95,
                    )
                )

            if "vue" in dependencies:
                frameworks.append(
                    FrameworkInfo(
                        primary="Vue.js",
                        version=dependencies["vue"],
                        confidence=0.95,
                    )
                )

            if "express" in dependencies:
                frameworks.append(
                    FrameworkInfo(
                        primary="Express.js",
                        version=dependencies["express"],
                        confidence=0.95,
                    )
                )

            return frameworks

        except Exception:
            return []

    async def _detect_python_frameworks(
        self, config_file_path: Path
    ) -> List[FrameworkInfo]:
        """Detect Python frameworks from config files."""
        frameworks = []

        try:
            if config_file_path.name == "pyproject.toml":
                async with aiofiles.open(config_file_path, encoding="utf-8") as f:
                    content = await f.read()
                    config_data = toml.loads(content)

                dependencies = config_data.get("project", {}).get("dependencies", [])

                for dep in dependencies:
                    if "django" in dep.lower():
                        frameworks.append(
                            FrameworkInfo(
                                primary="Django",
                                version="unknown",
                                confidence=0.90,
                            )
                        )
                    elif "fastapi" in dep.lower():
                        frameworks.append(
                            FrameworkInfo(
                                primary="FastAPI",
                                version="unknown",
                                confidence=0.90,
                            )
                        )
                    elif "flask" in dep.lower():
                        frameworks.append(
                            FrameworkInfo(
                                primary="Flask",
                                version="unknown",
                                confidence=0.90,
                            )
                        )

        except Exception:
            pass

        return frameworks

    async def _detect_rust_frameworks(
        self, cargo_toml_path: Path
    ) -> List[FrameworkInfo]:
        """Detect Rust frameworks from Cargo.toml."""
        try:
            async with aiofiles.open(cargo_toml_path, encoding="utf-8") as f:
                content = await f.read()
                cargo_data = toml.loads(content)

            frameworks = []
            dependencies = cargo_data.get("dependencies", {})

            if "axum" in dependencies:
                frameworks.append(
                    FrameworkInfo(
                        primary="Axum",
                        version=str(dependencies["axum"]),
                        confidence=0.95,
                    )
                )

            if "actix-web" in dependencies:
                frameworks.append(
                    FrameworkInfo(
                        primary="Actix Web",
                        version=str(dependencies["actix-web"]),
                        confidence=0.95,
                    )
                )

            return frameworks

        except Exception:
            return []

    async def _detect_java_frameworks(
        self, config_file_path: Path
    ) -> List[FrameworkInfo]:
        """Detect Java frameworks - simplified implementation."""
        # This would need more sophisticated parsing for XML/Gradle
        return []

    async def _detect_go_frameworks(self, go_mod_path: Path) -> List[FrameworkInfo]:
        """Detect Go frameworks from go.mod."""
        try:
            async with aiofiles.open(go_mod_path, encoding="utf-8") as f:
                content = await f.read()

            frameworks = []

            if "github.com/gin-gonic/gin" in content:
                frameworks.append(
                    FrameworkInfo(
                        primary="Gin",
                        version="unknown",
                        confidence=0.95,
                    )
                )

            if "github.com/gorilla/mux" in content:
                frameworks.append(
                    FrameworkInfo(
                        primary="Gorilla Mux",
                        version="unknown",
                        confidence=0.95,
                    )
                )

            return frameworks

        except Exception:
            return []

    async def _analyze_architecture_async(
        self, project_path: Path
    ) -> ArchitecturePattern:
        """Analyze architecture pattern asynchronously."""
        async with performance_monitor.track_operation("architecture_analysis"):
            # Run architecture detection in executor
            # Create mock parameters for compatibility
            filesystem_info = FileSystemInfo()
            language_info = LanguageInfo()
            framework_info = FrameworkInfo()
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self.architecture_detector.detect,
                project_path,
                filesystem_info,
                language_info,
                framework_info,
            )

    async def _analyze_domain_async(self, project_path: Path) -> DomainInfo:
        """Analyze domain information asynchronously."""
        async with performance_monitor.track_operation("domain_analysis"):
            # Run domain analysis in executor
            # Create mock filesystem_info and language_info for compatibility
            filesystem_info = FileSystemInfo()
            language_info = LanguageInfo()
            framework_info = FrameworkInfo()
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self.domain_detector.detect,
                project_path,
                filesystem_info,
                language_info,
                framework_info,
            )

    async def _determine_project_type_async(
        self,
        languages: List[LanguageInfo],
        frameworks: List[FrameworkInfo],
        filesystem_info: FileSystemInfo,
    ) -> ProjectType:
        """Determine project type based on analysis."""
        # Run in executor as it's CPU-bound logic
        return await asyncio.get_event_loop().run_in_executor(
            None,
            self._determine_project_type_sync,
            languages,
            frameworks,
            filesystem_info,
        )

    def _determine_project_type_sync(
        self,
        languages: List[LanguageInfo],
        frameworks: List[FrameworkInfo],
        filesystem_info: FileSystemInfo,
    ) -> ProjectType:
        """Synchronous project type determination logic."""
        # Simplified logic - in real implementation this would be more sophisticated
        web_frameworks = ["React", "Vue.js", "Django", "FastAPI", "Express.js"]
        api_frameworks = ["FastAPI", "Express.js", "Axum", "Actix Web"]

        for framework in frameworks:
            if hasattr(framework, "primary") and framework.primary in web_frameworks:
                return ProjectType.WEB_APPLICATION
            if hasattr(framework, "primary") and framework.primary in api_frameworks:
                return ProjectType.API_SERVICE

        # Check by language
        primary_language = languages[0] if languages else None
        if primary_language:
            if (
                primary_language.primary
                and primary_language.primary.lower() == "python"
            ):
                if any(
                    "django" in f.primary.lower()
                    for f in frameworks
                    if hasattr(f, "primary") and f.primary
                ):
                    return ProjectType.WEB_APPLICATION
                if any(
                    "fastapi" in f.primary.lower()
                    for f in frameworks
                    if hasattr(f, "primary") and f.primary
                ):
                    return ProjectType.API_SERVICE
                return ProjectType.LIBRARY
            if primary_language.primary and primary_language.primary.lower() == "rust":
                return ProjectType.CLI_TOOL

        return ProjectType.LIBRARY

    def _calculate_confidence_score(
        self,
        languages: List[LanguageInfo],
        frameworks: List[FrameworkInfo],
        architecture: ArchitecturePattern,
        domain_info: DomainInfo,
    ) -> float:
        """Calculate overall confidence score for the analysis."""
        total_confidence = 0.0
        count = 0

        # Language confidence
        if languages:
            avg_lang_confidence = sum(lang.confidence for lang in languages) / len(
                languages
            )
            total_confidence += avg_lang_confidence
            count += 1

        # Framework confidence
        if frameworks:
            avg_framework_confidence = sum(fw.confidence for fw in frameworks) / len(
                frameworks
            )
            total_confidence += avg_framework_confidence
            count += 1

        # Architecture confidence (simplified)
        if architecture != ArchitecturePattern.UNKNOWN:
            total_confidence += 75.0  # Base confidence for detected architecture
            count += 1

        return total_confidence / max(count, 1)

    def _detect_development_environment(
        self, filesystem_info: FileSystemInfo
    ) -> DevelopmentEnvironment:
        """Detect development environment from filesystem info."""
        root_files = filesystem_info.root_files

        # Check for containerization
        containerization = []
        if any("dockerfile" in f.lower() or "docker" in f.lower() for f in root_files):
            containerization.append("Docker")

        # Check for cloud deployment indicators
        if any(f.endswith((".yaml", ".yml")) for f in root_files):
            containerization.append("Kubernetes")

        return DevelopmentEnvironment(containerization=containerization)

    async def batch_analyze_async(
        self, project_paths: List[Union[str, Path]]
    ) -> List[ProjectAnalysis]:
        """Analyze multiple projects concurrently."""
        async with performance_monitor.track_operation("batch_analysis") as op:
            op["project_count"] = len(project_paths)

            # Create analysis tasks
            tasks = []
            for path in project_paths:
                task = asyncio.create_task(
                    self.analyze_async(path),
                    name=f"analyze_{Path(path).name}",
                )
                tasks.append(task)

            # Wait for all analyses with error handling
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            analyses: List[ProjectAnalysis] = []
            for result in results:
                if isinstance(result, Exception):
                    # Skip failed analyses
                    continue
                else:
                    analyses.append(result)  # type: ignore[arg-type]

            return analyses

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for analyzer operations."""
        return {
            "analyzer_config": {
                "max_concurrent_files": self.max_concurrent_files,
                "caching_enabled": self.enable_caching,
                "confidence_threshold": self.confidence_threshold,
            },
            "cache_stats": cache.get_stats(),
            "operation_metrics": performance_monitor.get_metrics(),
            "active_operations": performance_monitor.get_active_operations_count(),
        }
