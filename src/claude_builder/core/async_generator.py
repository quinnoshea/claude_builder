"""Async document generator for Claude Builder.

This module provides async implementations of document generation operations,
optimized for performance and concurrent template processing in Phase 3.4.
"""

import asyncio

from datetime import datetime
from pathlib import Path
from string import Template as StringTemplate
from typing import Any, Dict, List, Optional

import aiofiles

from claude_builder.core.agents import UniversalAgentSystem
from claude_builder.core.models import (
    GeneratedContent,
    ProjectAnalysis,
    TemplateRequest,
)
from claude_builder.core.template_management.network.async_template_downloader import (
    AsyncTemplateDownloader,
)
from claude_builder.core.template_manager import CoreTemplateManager
from claude_builder.utils.async_performance import (
    AsyncFileProcessor,
    cache,
    performance_monitor,
)
from claude_builder.utils.exceptions import GenerationError, PerformanceError


class AsyncDocumentGenerator:
    """Async document generator with performance optimization."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        *,
        max_concurrent_generations: int = 5,
        enable_caching: bool = True,
    ):
        """Initialize async generator.

        Args:
            config: Generator configuration
            max_concurrent_generations: Maximum concurrent generation operations
            enable_caching: Whether to enable template result caching
        """
        self.config = config or {}
        self.max_concurrent_generations = max_concurrent_generations
        self.enable_caching = enable_caching

        # Core components
        self.template_manager = CoreTemplateManager()
        self.agent_system = UniversalAgentSystem()
        self.async_downloader = AsyncTemplateDownloader()

        # Performance components
        self._file_processor = AsyncFileProcessor(
            max_concurrent_files=max_concurrent_generations
        )
        self._semaphore = asyncio.Semaphore(max_concurrent_generations)

    async def generate_async(
        self, analysis: ProjectAnalysis, output_path: Path
    ) -> GeneratedContent:
        """Generate all documentation asynchronously.

        Args:
            analysis: Project analysis results
            output_path: Directory to write generated files

        Returns:
            Generated content information
        """
        async with performance_monitor.track_operation(
            "async_document_generation"
        ) as op:
            op["project_name"] = analysis.project_path.name
            op["output_path"] = str(output_path)

            try:
                # Create output directory if needed
                output_path.mkdir(parents=True, exist_ok=True)

                # Create template request
                template_request = TemplateRequest(
                    analysis=analysis,
                    template_name=self.config.get("preferred_template"),
                    output_format=self.config.get("output_format", "files"),
                    customizations=self.config.get("customizations", {}),
                )

                # Generate content concurrently
                generation_tasks = [
                    self._generate_core_docs_async(analysis, output_path),
                    self._generate_agent_config_async(analysis, output_path),
                    self._generate_project_config_async(analysis, output_path),
                    self._generate_development_guides_async(analysis, output_path),
                ]

                results = await asyncio.gather(
                    *generation_tasks, return_exceptions=True
                )

                # Combine results
                generated_files = {}
                for result in results:
                    if isinstance(result, dict):
                        generated_files.update(result)
                    elif isinstance(result, Exception):
                        self._handle_generation_error(result)

                # Create generated content summary
                return GeneratedContent(
                    files=generated_files,
                    metadata={
                        "generation_timestamp": datetime.utcnow(),
                        "template_request": template_request,
                        "output_path": str(output_path),
                        "file_count": len(generated_files),
                    },
                )

            except Exception as e:
                raise GenerationError(f"Document generation failed: {e}") from e

    async def _generate_core_docs_async(
        self, analysis: ProjectAnalysis, output_path: Path
    ) -> Dict[str, str]:
        """Generate core documentation files asynchronously."""
        async with self._semaphore:
            async with performance_monitor.track_operation("generate_core_docs"):
                # Check cache first
                cache_key = (
                    f"core_docs:{analysis.project_path.name}:{hash(str(analysis))}"
                )
                if self.enable_caching:
                    cached_result = await cache.get(cache_key)
                    if cached_result is not None and isinstance(cached_result, dict):
                        await self._write_cached_files(cached_result, output_path)
                        return cached_result  # type: ignore[no-any-return]

                files = {}

                # Generate CLAUDE.md
                claude_content = await self._render_template_async(
                    "claude_md_template",
                    {
                        "project_name": analysis.project_path.name,
                        "project_type": analysis.project_type.value,
                        "languages": ([analysis.language] if analysis.language else [])
                        + analysis.language_info.secondary,
                        "frameworks": (
                            [analysis.framework] if analysis.framework else []
                        )
                        + analysis.framework_info.secondary,
                        "complexity": analysis.complexity_level.value,
                        "architecture": analysis.architecture_pattern.value,
                    },
                )

                claude_file = output_path / "CLAUDE.md"
                await self._write_file_async(claude_file, claude_content)
                files["CLAUDE.md"] = claude_content

                # Generate README additions
                readme_content = await self._render_template_async(
                    "readme_additions_template",
                    {
                        "project_name": analysis.project_path.name,
                        "setup_instructions": self._get_setup_instructions(analysis),
                        "development_workflow": self._get_development_workflow(
                            analysis
                        ),
                    },
                )

                readme_file = output_path / "README_ADDITIONS.md"
                await self._write_file_async(readme_file, readme_content)
                files["README_ADDITIONS.md"] = readme_content

                # Cache successful result
                if self.enable_caching:
                    await cache.set(cache_key, files)

                return files

    async def _generate_agent_config_async(
        self, analysis: ProjectAnalysis, output_path: Path
    ) -> Dict[str, str]:
        """Generate agent configuration asynchronously."""
        async with self._semaphore:
            async with performance_monitor.track_operation("generate_agent_config"):
                # Get optimal agent configuration
                agent_config = await asyncio.get_event_loop().run_in_executor(
                    None, self.agent_system.select_agents, analysis
                )

                # Render agent template
                agent_content = await self._render_template_async(
                    "agents_md_template",
                    {
                        "project_name": analysis.project_path.name,
                        "recommended_agents": [
                            agent.name for agent in agent_config.core_agents[:3]
                        ],  # Top 3 core agents
                        "workflow_patterns": list(
                            agent_config.coordination_patterns.keys()
                        ),
                        "coordination_strategy": "Agent-first development with specialized expertise",
                    },
                )

                agents_file = output_path / "AGENTS.md"
                await self._write_file_async(agents_file, agent_content)

                return {"AGENTS.md": agent_content}

    async def _generate_project_config_async(
        self, analysis: ProjectAnalysis, output_path: Path
    ) -> Dict[str, str]:
        """Generate project configuration files asynchronously."""
        async with self._semaphore:
            async with performance_monitor.track_operation("generate_project_config"):
                files = {}

                # Generate .gitignore if needed
                gitignore_content = await self._render_template_async(
                    "gitignore_template",
                    {
                        "languages": [
                            lang.lower()
                            for lang in (
                                ([analysis.language] if analysis.language else [])
                                + analysis.language_info.secondary
                            )
                        ],
                        "frameworks": [
                            fw.lower()
                            for fw in (
                                ([analysis.framework] if analysis.framework else [])
                                + analysis.framework_info.secondary
                            )
                        ],
                    },
                )

                gitignore_file = output_path / ".gitignore"
                if not gitignore_file.exists():  # Don't overwrite existing
                    await self._write_file_async(gitignore_file, gitignore_content)
                    files[".gitignore"] = gitignore_content

                # Generate development configuration
                if (analysis.language and analysis.language.lower() == "python") or any(
                    lang.lower() == "python"
                    for lang in analysis.language_info.secondary
                ):
                    pyproject_content = await self._render_template_async(
                        "pyproject_toml_template",
                        {
                            "project_name": analysis.project_path.name,
                            "frameworks": (
                                [analysis.framework] if analysis.framework else []
                            )
                            + analysis.framework_info.secondary,
                        },
                    )

                    pyproject_file = output_path / "pyproject.toml"
                    if not pyproject_file.exists():  # Don't overwrite
                        await self._write_file_async(pyproject_file, pyproject_content)
                        files["pyproject.toml"] = pyproject_content

                return files

    async def _generate_development_guides_async(
        self, analysis: ProjectAnalysis, output_path: Path
    ) -> Dict[str, str]:
        """Generate development guides asynchronously."""
        async with self._semaphore:
            async with performance_monitor.track_operation("generate_dev_guides"):
                files = {}

                # Generate CONTRIBUTING.md
                contributing_content = await self._render_template_async(
                    "contributing_template",
                    {
                        "project_name": analysis.project_path.name,
                        "languages": ([analysis.language] if analysis.language else [])
                        + analysis.language_info.secondary,
                        "frameworks": (
                            [analysis.framework] if analysis.framework else []
                        )
                        + analysis.framework_info.secondary,
                        "testing_strategy": self._get_testing_strategy(analysis),
                    },
                )

                contributing_file = output_path / "CONTRIBUTING.md"
                await self._write_file_async(contributing_file, contributing_content)
                files["CONTRIBUTING.md"] = contributing_content

                # Generate development workflow guide
                workflow_content = await self._render_template_async(
                    "development_workflow_template",
                    {
                        "project_name": analysis.project_path.name,
                        "complexity": analysis.complexity_level.value,
                        "agent_workflow": self._get_agent_workflow_guide(analysis),
                    },
                )

                workflow_file = output_path / "docs" / "DEVELOPMENT_WORKFLOW.md"
                workflow_file.parent.mkdir(exist_ok=True)
                await self._write_file_async(workflow_file, workflow_content)
                files["docs/DEVELOPMENT_WORKFLOW.md"] = workflow_content

                return files

    async def _render_template_async(
        self, template_name: str, context: Dict[str, Any]
    ) -> str:
        """Render template asynchronously with caching."""
        # Check template cache
        cache_key = f"template:{template_name}:{hash(str(context))}"
        if self.enable_caching:
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return str(cached_result)

        try:
            # Get template (in executor to avoid blocking)
            template_content = await asyncio.get_event_loop().run_in_executor(
                None, self._get_template_content, template_name
            )

            # Render template
            template = StringTemplate(template_content)
            rendered_content = template.safe_substitute(**context)

            # Cache successful result
            if self.enable_caching:
                await cache.set(cache_key, rendered_content)

            return rendered_content

        except Exception as e:
            raise GenerationError(
                f"Template rendering failed for {template_name}: {e}"
            ) from e

    def _get_template_content(self, template_name: str) -> str:
        """Get template content (synchronous helper)."""
        # This would interface with the actual template system
        # For now, return basic templates
        templates = {
            "claude_md_template": self._get_claude_md_template(),
            "readme_additions_template": self._get_readme_template(),
            "agents_md_template": self._get_agents_md_template(),
            "gitignore_template": self._get_gitignore_template(),
            "pyproject_toml_template": self._get_pyproject_template(),
            "contributing_template": self._get_contributing_template(),
            "development_workflow_template": self._get_workflow_template(),
        }

        return templates.get(template_name, "# Template not found: $template_name")

    async def _write_file_async(self, file_path: Path, content: str) -> None:
        """Write file asynchronously."""
        try:
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)
        except Exception as e:
            raise PerformanceError(f"Failed to write file {file_path}: {e}") from e

    async def _write_cached_files(
        self, cached_files: Dict[str, str], output_path: Path
    ) -> None:
        """Write cached files to disk asynchronously."""
        write_tasks = []

        for filename, content in cached_files.items():
            file_path = output_path / filename
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            task = asyncio.create_task(self._write_file_async(file_path, content))
            write_tasks.append(task)

        await asyncio.gather(*write_tasks)

    def _handle_generation_error(self, error: Exception) -> None:
        """Handle generation errors."""
        if isinstance(error, (GenerationError, PerformanceError)):
            raise error
        raise GenerationError(f"Unexpected generation error: {error}") from error

    # Helper methods for template context
    def _get_setup_instructions(self, analysis: ProjectAnalysis) -> str:
        """Get setup instructions based on analysis."""
        instructions = []

        languages = (
            [analysis.language] if analysis.language else []
        ) + analysis.language_info.secondary
        for lang in languages:
            if lang.lower() == "python":
                instructions.append("pip install -r requirements.txt")
            elif lang.lower() in ["javascript", "typescript", "node"]:
                instructions.append("npm install")
            elif lang.lower() == "rust":
                instructions.append("cargo build")

        return "\n".join(instructions)

    def _get_development_workflow(self, analysis: ProjectAnalysis) -> str:
        """Get development workflow based on analysis."""
        return f"""1. Clone the repository
2. Set up development environment
3. Run tests: {self._get_test_command(analysis)}
4. Start development server (if applicable)
5. Make changes and create pull request"""

    def _get_test_command(self, analysis: ProjectAnalysis) -> str:
        """Get test command based on analysis."""
        languages = (
            [analysis.language] if analysis.language else []
        ) + analysis.language_info.secondary
        for lang in languages:
            if lang.lower() == "python":
                return "pytest"
            if lang.lower() in ["javascript", "typescript", "node"]:
                return "npm test"
            if lang.lower() == "rust":
                return "cargo test"
        return "# Add test command here"

    def _get_testing_strategy(self, analysis: ProjectAnalysis) -> str:
        """Get testing strategy based on analysis."""
        strategies = []

        if analysis.complexity_level.value in ["high", "very_high"]:
            strategies.append("Comprehensive unit testing")
            strategies.append("Integration testing")
            strategies.append("End-to-end testing")
        else:
            strategies.append("Unit testing")
            strategies.append("Basic integration testing")

        return "\n".join(f"- {strategy}" for strategy in strategies)

    def _get_agent_workflow_guide(self, analysis: ProjectAnalysis) -> str:
        """Get agent workflow guide based on analysis."""
        return f"""## Agent-Driven Development Workflow

### Recommended Agent Usage for {analysis.project_path.name}

1. **Analysis Phase**: Use `rapid-prototyper` for initial development
2. **Implementation Phase**: Use appropriate agents based on:
   - Languages: {', '.join(([analysis.language] if analysis.language else []) + analysis.language_info.secondary)}
   - Frameworks: {', '.join(([analysis.framework] if analysis.framework else []) + analysis.framework_info.secondary)}
3. **Testing Phase**: Use `test-writer-fixer` for comprehensive testing
4. **Documentation Phase**: Use `documentation-engineer` for final docs

### Performance Optimization
- Leverage async operations for I/O-heavy tasks
- Use concurrent agent coordination for complex workflows
- Monitor performance with built-in metrics"""

    # Template content methods (simplified)
    def _get_claude_md_template(self) -> str:
        return """# CLAUDE.md

## Project: $project_name

### Project Type
$project_type

### Languages
$languages

### Frameworks
$frameworks

### Architecture
$architecture

### Complexity Level
$complexity

## Development Guidelines

This project uses Claude Builder for optimal Claude Code integration.
"""

    def _get_readme_template(self) -> str:
        return """# $project_name

## Setup Instructions

$setup_instructions

## Development Workflow

$development_workflow
"""

    def _get_agents_md_template(self) -> str:
        return """# AGENTS.md - Claude Code Agent Configuration

## Project: $project_name

### Recommended Agents
$recommended_agents

### Workflow Patterns
$workflow_patterns

### Coordination Strategy
$coordination_strategy
"""

    def _get_gitignore_template(self) -> str:
        return """# Language-specific ignores
# Generated based on: $languages, $frameworks

# Python
__pycache__/
*.pyc
.venv/

# Node.js
node_modules/
npm-debug.log*

# Rust
target/
Cargo.lock

# General
.DS_Store
*.log
.env
"""

    def _get_pyproject_template(self) -> str:
        return """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "$project_name"
version = "0.1.0"
description = "Project generated with Claude Builder"
"""

    def _get_contributing_template(self) -> str:
        return """# Contributing to $project_name

## Testing Strategy
$testing_strategy

## Development Process
1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests
5. Submit pull request
"""

    def _get_workflow_template(self) -> str:
        return """# Development Workflow for $project_name

## Complexity Level: $complexity

$agent_workflow
"""

    async def batch_generate_async(
        self, analyses: List[ProjectAnalysis], base_output_path: Path
    ) -> List[GeneratedContent]:
        """Generate documentation for multiple projects concurrently."""
        async with performance_monitor.track_operation("batch_generation") as op:
            op["project_count"] = len(analyses)

            # Create generation tasks
            tasks = []
            for analysis in analyses:
                project_output_path = base_output_path / analysis.project_path.name
                task = asyncio.create_task(
                    self.generate_async(analysis, project_output_path),
                    name=f"generate_{analysis.project_path.name}",
                )
                tasks.append(task)

            # Wait for all generations
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            generated_contents: List[GeneratedContent] = []
            for result in results:
                if isinstance(result, Exception):
                    # Skip errors for now - could create error report
                    continue
                if result is not None:
                    generated_contents.append(result)  # type: ignore[arg-type]

            return generated_contents

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for generator operations."""
        return {
            "generator_config": {
                "max_concurrent_generations": self.max_concurrent_generations,
                "caching_enabled": self.enable_caching,
            },
            "cache_stats": cache.get_stats(),
            "operation_metrics": performance_monitor.get_metrics(),
            "template_manager_stats": getattr(
                self.template_manager, "get_stats", dict
            )(),
        }
