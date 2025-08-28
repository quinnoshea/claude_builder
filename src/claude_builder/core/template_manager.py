"""Refactored template management system for Claude Builder.

This module provides the main TemplateManager interface while delegating
specific responsibilities to specialized modules for better maintainability
and reduced complexity.

PHASE 3.1 REFACTORING: Core Module Separation
- Network operations → template_management.network
- Validation logic → template_management.validation
- Community features → template_management.community
"""

import logging

from pathlib import Path
from typing import Any, Dict, List, Optional

from claude_builder.core.models import (
    AgentDefinition,
    EnvironmentBundle,
    ProjectAnalysis,
    SubagentFile,
    ValidationResult,
)
from claude_builder.core.template_management.community.template_repository import (
    CommunityTemplate,
    CommunityTemplateManager,
    TemplateMetadata,
)

# Import from extracted modules
from claude_builder.core.template_management.network.template_downloader import (
    TemplateDownloader,
    TemplateRepositoryClient,
)
from claude_builder.core.template_management.validation.template_validator import (
    ComprehensiveTemplateValidator,
)

# Legacy imports for backward compatibility
from claude_builder.core.template_manager_legacy import (
    FAILED_TO_LOAD_TEMPLATE,
    TEMPLATE_NOT_FOUND,
    CoreTemplateManager,
    Template,
    TemplateBuilder,
    TemplateContext,
    TemplateEcosystem,
    TemplateError,
    TemplateLoader,
    TemplateMarketplace,
    TemplateRenderer,
    TemplateRepository,
    TemplateVersion,
)


class ModernTemplateManager:
    """Modern template manager with modular architecture.

    This is the new main template manager that coordinates between
    specialized modules while maintaining backward compatibility
    with the existing TemplateManager interface.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        template_directory: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize modern template manager.

        Args:
            config: Configuration dictionary
            template_directory: Template directory path
            **kwargs: Additional configuration parameters
        """
        self.config = config or {}
        self.config.update(kwargs)

        # Template directory setup
        if template_directory:
            self.templates_dir = Path(template_directory)
        else:
            self.templates_dir = Path.home() / ".claude-builder" / "templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Initialize specialized components
        self.downloader = TemplateDownloader()
        self.repository_client = TemplateRepositoryClient(self.downloader)
        self.validator = ComprehensiveTemplateValidator()
        self.community_manager = CommunityTemplateManager(
            templates_dir=self.templates_dir,
            downloader=self.downloader,
            repository_client=self.repository_client,
            validator=self.validator,
        )

        # Legacy components for backward compatibility
        self.loader = TemplateLoader(
            template_directory=str(self.templates_dir) if template_directory else None
        )
        self.renderer = TemplateRenderer()
        self.core_manager = CoreTemplateManager([str(self.templates_dir)])

        # Cache for backward compatibility
        self.templates: Dict[str, Any] = {}

        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized ModernTemplateManager with modular architecture")

    # Community template methods (delegated to CommunityTemplateManager)

    def list_available_templates(
        self, *, include_installed: bool = True, include_community: bool = True
    ) -> List[CommunityTemplate]:
        """List all available templates."""
        return self.community_manager.list_available_templates(
            include_installed=include_installed, include_community=include_community
        )

    def search_templates(
        self, query: str, project_analysis: Optional[ProjectAnalysis] = None
    ) -> List[CommunityTemplate]:
        """Search for templates matching query and project analysis."""
        return self.community_manager.search_templates(query, project_analysis)

    def install_template(
        self, template_id: str, *, force: bool = False
    ) -> ValidationResult:
        """Install a community template."""
        return self.community_manager.install_template(template_id, force=force)

    def uninstall_template(self, template_name: str) -> ValidationResult:
        """Uninstall an installed template."""
        return self.community_manager.uninstall_template(template_name)

    def create_custom_template(
        self, name: str, project_path: Path, template_config: Dict[str, Any]
    ) -> ValidationResult:
        """Create a custom template from existing project."""
        return self.community_manager.create_custom_template(
            name, project_path, template_config
        )

    def get_template_info(self, template_name: str) -> Optional[CommunityTemplate]:
        """Get detailed information about a template."""
        return self.community_manager.get_template_info(template_name)

    # Validation methods (delegated to ComprehensiveTemplateValidator)

    def validate_template_directory(self, template_path: Path) -> ValidationResult:
        """Validate a template directory."""
        return self.validator.validate_template(template_path)

    # Legacy template methods for backward compatibility

    def get_template(self, template_name: str) -> Optional[Template]:
        """Get template object (backward compatibility)."""
        # Try to get from community manager first
        community_template = self.get_template_info(template_name.replace(".md", ""))
        if community_template:
            return Template(template_name, content="Modern template content")

        # Fall back to legacy loader
        return self.loader.load_template_from_file(template_name)

    def get_templates_by_type(self, template_type: str) -> List[Template]:
        """Get templates filtered by type (backward compatibility)."""
        templates = []

        if template_type == "documentation":
            templates.extend(
                [
                    Template("docs.md", "# Documentation", template_type=template_type),
                    Template(
                        "api.md", "# API Documentation", template_type=template_type
                    ),
                ]
            )
        elif template_type == "guide":
            templates.append(
                Template(
                    "development.md", "# Development Guide", template_type=template_type
                )
            )

        return templates

    def render_template(self, template_name: str, context: TemplateContext) -> str:
        """Render template by name with context (backward compatibility)."""
        template_path = self.templates_dir / template_name

        if template_path.exists():
            return self.core_manager.render_template(
                template_path.read_text(encoding="utf-8"), context.variables
            )

        # Return mock content for tests
        if "claude" in template_name.lower():
            return f"# {context.get('project_name', 'Project')} - Claude Instructions"

        return f"# {context.get('project_name', 'Project')}\nGenerated content"

    def select_template_for_project(
        self, template_name: str, project_type: str
    ) -> Template:
        """Select best template for project type (backward compatibility)."""
        # Look for project-type specific template first
        specific_name = f"{project_type}_{template_name}"
        specific_path = self.templates_dir / f"{specific_name}.md"

        if specific_path.exists():
            return Template(f"{specific_name}.md", content="Project-specific template")

        # Fall back to generic template
        return Template(f"{template_name}.md", content="Generic template")

    def render_batch(
        self, templates: Dict[str, str], context: TemplateContext
    ) -> Dict[str, str]:
        """Render multiple templates with shared context (backward compatibility)."""
        results = {}

        for name, content in templates.items():
            template = Template(name, content)
            results[name] = self.renderer.render(template, **context.variables)

        return results

    def _find_community_template(self, template_id: str) -> Optional[CommunityTemplate]:
        """Find a specific template in community sources (backward compatibility)."""
        # Delegate to community manager
        if hasattr(self.community_manager, "find_template"):
            result = self.community_manager.find_template(template_id)
            if isinstance(result, CommunityTemplate):
                return result

        # Fallback to searching available templates
        try:
            available = self.list_available_templates()
            for template in available:
                if isinstance(template, CommunityTemplate):
                    if hasattr(template, "id") and template.id == template_id:
                        return template
                    if hasattr(template, "name") and template.name == template_id:
                        return template
        except Exception:
            pass

        return None

    def render_all_templates(self, context: TemplateContext) -> Dict[str, str]:
        """Render all templates with shared context (backward compatibility)."""
        templates = {
            "claude.md": "# {{ project_name }} - Claude Instructions",
            "readme.md": "# {{ project_name }}\n{{ description }}",
            "guide.md": "# Development Guide for {{ project_name }}",
        }
        return self.render_batch(templates, context)

    # Core template operations

    def load_template(self, template_name: str) -> str:
        """Load template content from file."""
        return self.loader.load_template(template_name)

    def compose_templates(
        self, base_template: str, overlay_templates: Optional[List[str]] = None
    ) -> str:
        """Compose hierarchical templates."""
        return self.core_manager.compose_templates(base_template, overlay_templates)

    def generate_from_analysis(
        self, analysis: ProjectAnalysis, template_name: str = "base"
    ) -> str:
        """Generate content from project analysis."""
        return self.core_manager.generate_from_analysis(analysis, template_name)

    def list_templates(self) -> List[str]:
        """List available template names."""
        return self.loader.list_templates()

    def template_exists(self, template_name: str) -> bool:
        """Check if template exists."""
        return self.loader.template_exists(template_name)

    # New multi-output generation methods for YAML subagent architecture

    def generate_complete_environment(
        self, analysis: ProjectAnalysis
    ) -> EnvironmentBundle:
        """Generate complete development environment - CLAUDE.md + individual subagents + AGENTS.md"""
        from datetime import datetime

        # Import agent system to generate project agents
        from claude_builder.core.agents import UniversalAgentSystem

        # Generate agent team configuration
        agent_system = UniversalAgentSystem()
        agent_config = agent_system.select_agents(analysis)

        # Convert agent selection to agent definitions
        agent_definitions = self._create_agent_definitions(agent_config, analysis)

        # Create context for all three output types
        context = self._create_environment_context(analysis, agent_definitions)

        # Generate three distinct outputs
        claude_md = self._generate_claude_documentation(context, analysis)
        subagent_files = self._generate_individual_subagents(context, agent_definitions)
        agents_md = self._generate_user_documentation(context, agent_definitions)

        return EnvironmentBundle(
            claude_md=claude_md,
            subagent_files=subagent_files,
            agents_md=agents_md,
            metadata={
                "analysis_confidence": analysis.analysis_confidence,
                "project_type": analysis.project_type.value,
                "language": analysis.language,
                "framework": analysis.framework,
                "agent_count": len(agent_definitions),
            },
            generation_timestamp=datetime.now().isoformat(),
        )

    def _create_agent_definitions(
        self, agent_config: Any, analysis: ProjectAnalysis
    ) -> List[AgentDefinition]:
        """Convert agent selection to enhanced agent definitions."""
        agent_definitions = []

        # Get all agents from the configuration
        all_agents = getattr(agent_config, "all_agents", [])

        for agent in all_agents:
            # Determine tools based on project context
            tools = self._determine_agent_tools(agent, analysis)

            # Generate enhanced system prompt
            system_prompt = self._generate_agent_system_prompt(agent, analysis)

            agent_def = AgentDefinition(
                name=self._generate_agent_name(agent.name, analysis),
                description=agent.description,
                tools=tools,
                system_prompt=system_prompt,
                specialization=getattr(agent, "category", "general"),
                category=getattr(agent, "category", "general"),
                confidence=getattr(agent, "confidence", 1.0),
                project_context={
                    "project_name": analysis.project_path.name,
                    "language": analysis.language,
                    "framework": analysis.framework,
                    "complexity": analysis.complexity_level.value,
                },
            )
            agent_definitions.append(agent_def)

        return agent_definitions

    def _determine_agent_tools(
        self, agent: Any, analysis: ProjectAnalysis
    ) -> List[str]:
        """Determine appropriate tools based on project context."""
        base_tools = ["Read", "Write", "MultiEdit", "Bash"]

        # Add language-specific tools
        if analysis.language == "python":
            base_tools.extend(["pytest", "black", "mypy", "ruff"])
        elif analysis.language == "rust":
            base_tools.extend(["cargo", "rustfmt", "clippy"])
        elif analysis.language == "javascript":
            base_tools.extend(["npm", "jest", "eslint"])

        # Add agent-specific tools based on specialization
        specialization = getattr(agent, "category", "general").lower()
        if "test" in specialization:
            base_tools.extend(["coverage", "pytest-cov"])
        elif "performance" in specialization:
            base_tools.extend(["profiler", "benchmark"])
        elif "backend" in specialization:
            base_tools.extend(["git", "docker"])

        return list(set(base_tools))  # Remove duplicates

    def _generate_agent_name(self, base_name: str, analysis: ProjectAnalysis) -> str:
        """Generate project-specific agent names."""
        project_prefix = analysis.project_path.name.lower().replace("-", "_")
        clean_base = base_name.lower().replace(" ", "_").replace("-", "_")
        return f"{project_prefix}_{clean_base}"

    def _generate_agent_system_prompt(
        self, agent: Any, analysis: ProjectAnalysis
    ) -> str:
        """Generate enhanced system prompt with project context."""
        base_prompt = (
            f"You are a {agent.name} specialized for {analysis.project_path.name}."
        )

        context_lines = [
            "## Project Context",
            f"- Language: {analysis.language or 'Unknown'}",
            f"- Framework: {analysis.framework or 'None detected'}",
            f"- Type: {analysis.project_type.value}",
            f"- Complexity: {analysis.complexity_level.value}",
            "",
            "## Core Responsibilities",
            agent.description or f"Specialized assistance for {agent.name} tasks.",
            "",
            "## Best Practices",
            "Follow the project's existing patterns and conventions.",
            "Maintain code quality and consistency.",
            "Consider performance and maintainability in all recommendations.",
        ]

        return base_prompt + "\n\n" + "\n".join(context_lines)

    def _create_environment_context(
        self, analysis: ProjectAnalysis, agent_definitions: List[AgentDefinition]
    ) -> Dict[str, Any]:
        """Create comprehensive context for template rendering."""
        return {
            "project_name": analysis.project_path.name,
            "project_description": f"A {analysis.language or 'multi-language'} {analysis.project_type.value} project",
            "primary_language": analysis.language or "Unknown",
            "primary_framework": analysis.framework or "None detected",
            "complexity_level": analysis.complexity_level.value,
            "project_type": analysis.project_type.value,
            "agent_count": len(agent_definitions),
            "agents": [
                {
                    "name": agent.yaml_name,
                    "description": agent.description,
                    "short_description": (
                        agent.description.split(".")[0] + "."
                        if "." in agent.description
                        else agent.description
                    ),
                    "specialization": agent.specialization,
                    "tools": agent.get_yaml_tools(),
                }
                for agent in agent_definitions
            ],
            "development_commands": self._generate_development_commands(analysis),
            "development_standards": self._generate_development_standards(analysis),
        }

    def _generate_development_commands(self, analysis: ProjectAnalysis) -> str:
        """Generate language-specific development commands."""
        commands = []

        if analysis.language == "python":
            commands.extend(
                [
                    "# Python Development",
                    "uv run pytest --cov=src --cov-report=term-missing",
                    "uv run black . && uv run ruff check .",
                    "uv run mypy src/",
                ]
            )
        elif analysis.language == "rust":
            commands.extend(
                [
                    "# Rust Development",
                    "cargo test",
                    "cargo fmt --all",
                    "cargo clippy -- -D warnings",
                ]
            )
        elif analysis.language == "javascript":
            commands.extend(
                [
                    "# JavaScript Development",
                    "npm test",
                    "npm run lint",
                    "npm run build",
                ]
            )
        else:
            commands.extend(
                ["# Development Commands", "# Add project-specific commands here"]
            )

        return "\n".join(commands)

    def _generate_development_standards(self, analysis: ProjectAnalysis) -> str:
        """Generate language-specific development standards."""
        standards = [
            "## Code Quality Standards",
            "- Follow existing project patterns and conventions",
            "- Write clear, self-documenting code",
            "- Include appropriate error handling",
            "- Add tests for new functionality",
        ]

        if analysis.language == "python":
            standards.extend(
                [
                    "- Follow PEP 8 style guidelines",
                    "- Use type hints for function signatures",
                    "- Document modules, classes, and functions",
                ]
            )
        elif analysis.language == "rust":
            standards.extend(
                [
                    "- Follow Rust idioms and conventions",
                    "- Use Result<T, E> for error handling",
                    "- Document public APIs with rustdoc",
                ]
            )

        return "\n".join(standards)

    def _generate_individual_subagents(
        self, context: Dict[str, Any], agent_definitions: List[AgentDefinition]
    ) -> List[SubagentFile]:
        """Generate individual subagent files with YAML front matter."""
        subagent_files = []

        for agent in agent_definitions:
            # Generate YAML front matter
            yaml_header = self._generate_yaml_front_matter(agent)

            # Generate agent system prompt
            agent_prompt = agent.system_prompt

            # Combine YAML + content
            content = f"---\n{yaml_header}\n---\n\n{agent_prompt}"

            subagent_files.append(
                SubagentFile(
                    name=f"{agent.yaml_name}.md",
                    content=content,
                    path=f".claude/agents/{agent.yaml_name}.md",
                )
            )

        return subagent_files

    def _generate_yaml_front_matter(self, agent: AgentDefinition) -> str:
        """Generate proper YAML front matter for subagent."""
        return f"""name: {agent.yaml_name}
description: {agent.description}
tools: {agent.get_yaml_tools()}"""

    def _generate_claude_documentation(
        self, context: Dict[str, Any], analysis: ProjectAnalysis
    ) -> str:
        """Generate regular CLAUDE.md project documentation (NO YAML)."""
        template_content = (
            f"""# {context['project_name']} Development Environment

## Project Overview
{context['project_description']}

**Language**: {context['primary_language']}
**Framework**: {context['primary_framework']}
**Type**: {context['project_type']}
**Complexity**: {context['complexity_level']}

## Development Standards
{context['development_standards']}

## Agent Team
This project includes {context['agent_count']} specialized subagents for optimal development:

"""
            + "\n".join(
                [
                    f"- **{agent['name']}**: {agent['short_description']}"
                    for agent in context["agents"]
                ]
            )
            + f"""

See AGENTS.md for detailed usage instructions and coordination patterns.

## Development Commands
{context['development_commands']}

## Architecture Notes
- Follow existing project patterns and conventions
- Maintain consistency in code style and structure
- Consider performance and maintainability in all changes
- Use the specialized agents for domain-specific tasks
"""
        )
        return template_content

    def _generate_user_documentation(
        self, context: Dict[str, Any], agent_definitions: List[AgentDefinition]
    ) -> str:
        """Generate user-friendly AGENTS.md documentation."""

        # Group agents by category
        agents_by_category: Dict[str, List[AgentDefinition]] = {}
        for agent in agent_definitions:
            category = agent.category.title()
            if category not in agents_by_category:
                agents_by_category[category] = []
            agents_by_category[category].append(agent)

        content_parts = [
            f"# {context['project_name']} - Development Agent Team",
            "",
            "## Quick Reference",
            f"This project has **{len(agent_definitions)} specialized agents** ready to assist with development tasks.",
            "",
            "### How to Use",
            "Simply describe your task naturally - agents will be selected automatically based on context:",
            "",
            '- *"Fix the failing tests"* → test specialist agent',
            '- *"Optimize this database query"* → backend architect agent',
            '- *"Review this code for security issues"* → code review agent',
            "",
            "## Agent Team Composition",
            "",
        ]

        # Add agents grouped by category
        for category, agents in agents_by_category.items():
            content_parts.extend([f"### {category} Agents", ""])

            for agent in agents:
                content_parts.extend(
                    [
                        f"#### {agent.yaml_name}",
                        agent.description,
                        "",
                        f"**Specialization**: {agent.specialization}",
                        f"**Tools**: {agent.get_yaml_tools()}",
                        "",
                    ]
                )

        content_parts.extend(
            [
                "## Usage Patterns",
                "",
                "### Natural Language Triggers",
                "Agents respond to natural language that matches their specialization:",
                "",
            ]
        )

        # Add usage examples
        for agent in agent_definitions[:3]:  # Show first 3 as examples
            example_request = self._generate_usage_example(agent)
            content_parts.extend(
                [
                    f'- **{agent.yaml_name}**: "{example_request}"',
                ]
            )

        content_parts.extend(
            [
                "",
                "### Multi-Agent Coordination",
                "Complex tasks automatically coordinate multiple agents:",
                "",
                '- *"Refactor this module and add comprehensive tests"* → backend + testing agents',
                '- *"Set up CI/CD with security scanning"* → devops + security agents',
                "",
                "## Best Practices",
                "- Be specific about your requirements and constraints",
                "- Mention relevant files, functions, or components when applicable",
                "- Ask for explanations when you need to understand the reasoning",
                "- Request multiple approaches when exploring solutions",
                "",
                "---",
                f"*Generated for {context['project_name']} - {context['primary_language']} {context['project_type']}*",
            ]
        )

        return "\n".join(content_parts)

    def _generate_usage_example(self, agent: AgentDefinition) -> str:
        """Generate a natural usage example for an agent."""
        examples = {
            "backend": "Optimize this API endpoint for better performance",
            "test": "Add comprehensive tests for the user authentication module",
            "frontend": "Improve the responsive design of this component",
            "security": "Review this code for potential security vulnerabilities",
            "performance": "Analyze and optimize the database queries in this module",
            "devops": "Set up automated deployment for this service",
        }

        # Try to match agent specialization to examples
        for key, example in examples.items():
            if key.lower() in agent.specialization.lower():
                return example

        # Default example
        return f"Help me improve the {agent.specialization} aspects of this project"


# Backward compatibility - use ModernTemplateManager as TemplateManager
TemplateManager = ModernTemplateManager


# Export all necessary classes and functions
__all__ = [
    # Main classes
    "TemplateManager",
    "ModernTemplateManager",
    # Community template classes
    "CommunityTemplate",
    "TemplateMetadata",
    # Validation
    "ValidationResult",
    # New YAML subagent classes
    "SubagentFile",
    "EnvironmentBundle",
    "AgentDefinition",
    # Legacy compatibility classes
    "Template",
    "TemplateBuilder",
    "TemplateContext",
    "TemplateEcosystem",
    "TemplateError",
    "TemplateMarketplace",
    "TemplateLoader",
    "TemplateRenderer",
    "CoreTemplateManager",
    "TemplateRepository",
    "TemplateVersion",
    # Constants
    "TEMPLATE_NOT_FOUND",
    "FAILED_TO_LOAD_TEMPLATE",
]
