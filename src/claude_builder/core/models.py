"""Data models for Claude Builder."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


DEPENDENCY_NAME_CANNOT_BE_EMPTY = "Dependency name cannot be empty"
INVALID_DEPENDENCY_TYPE = "Invalid dependency type"
PATH_CANNOT_BE_EMPTY = "Path cannot be empty"
INVALID_FILE_TYPE = "Invalid file type"
INVALID_OUTPUT_FORMAT = "Invalid output format"
INVALID_TEMPLATE_VARIANT = "Invalid template variant"
PROJECT_NAME_CANNOT_BE_EMPTY = "Project name cannot be empty"
INVALID_PROJECT_TYPE = "Invalid project type"


class ProjectType(Enum):
    """Detected project types."""

    WEB_APPLICATION = "web_application"
    WEB_FRONTEND = "web_frontend"  # Add for test compatibility
    API_SERVICE = "api_service"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    DATA_SCIENCE = "data_science"
    MICROSERVICE = "microservice"
    MONOREPO = "monorepo"
    DESKTOP_APP = "desktop_app"
    MOBILE_APP = "mobile_app"
    GAME = "game"
    APPLICATION = "application"  # Generic application type
    UNKNOWN = "unknown"


class ComplexityLevel(Enum):
    """Project complexity levels."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    MEDIUM = "moderate"  # Alias for test compatibility
    COMPLEX = "complex"
    HIGH = "complex"  # Alias for test compatibility
    ENTERPRISE = "enterprise"


class ArchitecturePattern(Enum):
    """Architecture patterns."""

    MVC = "mvc"
    MICROSERVICES = "microservices"
    MONOLITH = "monolith"
    SERVERLESS = "serverless"
    EVENT_DRIVEN = "event_driven"
    DOMAIN_DRIVEN = "domain_driven"
    LAYERED = "layered"
    HEXAGONAL = "hexagonal"
    UNKNOWN = "unknown"


@dataclass
class LanguageInfo:
    """Information about detected languages."""

    primary: Optional[str] = None
    secondary: List[str] = field(default_factory=list)
    confidence: float = 0.0
    file_counts: Dict[str, int] = field(default_factory=dict)
    total_lines: Dict[str, int] = field(default_factory=dict)
    # Optional version information keyed by language name (e.g., {"python": "3.11"})
    version_info: Dict[str, str] = field(default_factory=dict)


@dataclass
class FrameworkInfo:
    """Information about detected frameworks."""

    primary: Optional[str] = None
    secondary: List[str] = field(default_factory=list)
    confidence: float = 0.0
    version: Optional[str] = None
    config_files: List[str] = field(default_factory=list)
    # Arbitrary details map (e.g., {"web_framework": True, "dependencies": [...]})
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DomainInfo:
    """Information about application domain."""

    domain: Optional[str] = None
    confidence: float = 0.0
    indicators: List[str] = field(default_factory=list)
    specialized_patterns: List[str] = field(default_factory=list)


@dataclass
class ToolMetadata:
    """Rich metadata describing a detected DevOps/MLOps tool."""

    name: str
    slug: str
    category: str
    confidence: str = "unknown"
    score: Optional[float] = None
    files: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class DevelopmentEnvironment:
    """Information about development environment and tools."""

    package_managers: List[str] = field(default_factory=list)
    testing_frameworks: List[str] = field(default_factory=list)
    linting_tools: List[str] = field(default_factory=list)
    ci_cd_systems: List[str] = field(default_factory=list)
    containerization: List[str] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    documentation_tools: List[str] = field(default_factory=list)
    # Phase 1 additions (P1.3): DevOps/MLOps facets
    infrastructure_as_code: List[str] = field(default_factory=list)
    orchestration_tools: List[str] = field(default_factory=list)
    secrets_management: List[str] = field(default_factory=list)
    observability: List[str] = field(default_factory=list)
    data_pipeline: List[str] = field(default_factory=list)
    mlops_tools: List[str] = field(default_factory=list)
    security_tools: List[str] = field(default_factory=list)
    tool_details: Dict[str, ToolMetadata] = field(default_factory=dict)


@dataclass
class FileSystemInfo:
    """Information about project file system structure."""

    total_files: int = 0
    total_directories: int = 0
    source_files: int = 0
    test_files: int = 0
    config_files: int = 0
    documentation_files: int = 0
    asset_files: int = 0
    ignore_patterns: List[str] = field(default_factory=list)
    root_files: List[str] = field(default_factory=list)
    directory_structure: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectAnalysis:
    """Complete project analysis results."""

    project_path: Path
    language_info: LanguageInfo = field(default_factory=LanguageInfo)
    framework_info: FrameworkInfo = field(default_factory=FrameworkInfo)
    domain_info: DomainInfo = field(default_factory=DomainInfo)
    project_type: ProjectType = ProjectType.UNKNOWN
    complexity_level: ComplexityLevel = ComplexityLevel.SIMPLE
    architecture_pattern: ArchitecturePattern = ArchitecturePattern.UNKNOWN
    dev_environment: DevelopmentEnvironment = field(
        default_factory=DevelopmentEnvironment
    )
    filesystem_info: FileSystemInfo = field(default_factory=FileSystemInfo)
    # Convenience attributes commonly asserted in tests
    build_system: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

    # Analysis metadata
    analysis_confidence: float = 0.0
    analysis_timestamp: Optional[str] = None
    analyzer_version: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    # Agent configuration (supports both modern and legacy containers)
    if TYPE_CHECKING:
        from claude_builder.core.agents import AgentConfiguration  # pragma: no cover
    agent_configuration: Optional["AgentConfiguration | AgentSelection"] = None

    @property
    def language(self) -> Optional[str]:
        """Primary language shorthand."""
        return self.language_info.primary

    @property
    def framework(self) -> Optional[str]:
        """Primary framework shorthand."""
        return self.framework_info.primary

    @property
    def has_tests(self) -> bool:
        """Whether project has test files."""
        return self.filesystem_info.test_files > 0

    @property
    def has_ci_cd(self) -> bool:
        """Whether project has CI/CD configured."""
        return len(self.dev_environment.ci_cd_systems) > 0

    @property
    def is_containerized(self) -> bool:
        """Whether project uses containerization."""
        return len(self.dev_environment.containerization) > 0

    @property
    def is_web_project(self) -> bool:
        """Check if this is a web-related project."""
        return self.project_type in [
            ProjectType.WEB_APPLICATION,
            ProjectType.API_SERVICE,
        ]

    @property
    def is_cli_project(self) -> bool:
        """Check if this is a CLI tool project."""
        return self.project_type == ProjectType.CLI_TOOL

    @property
    def uses_database(self) -> bool:
        """Check if project uses a database."""
        return len(self.dev_environment.databases) > 0

    # Removed duplicate properties - they already exist above


class ClaudeMentionPolicy(Enum):
    """Policies for Claude mentions in generated content."""

    ALLOWED = "allowed"  # Full Claude attribution
    MINIMAL = "minimal"  # Minimal references, only in dev docs
    FORBIDDEN = "forbidden"  # No Claude references anywhere


class GitIntegrationMode(Enum):
    """Git integration modes."""

    NO_INTEGRATION = "no_integration"
    EXCLUDE_GENERATED = "exclude_generated"
    TRACK_GENERATED = "track_generated"


@dataclass
class AgentInfo:
    """Information about an agent."""

    name: str
    description: str = ""
    category: str = "general"
    # Default confidence should start at 0.0; tests rely on this
    confidence: float = 0.0

    # Additional fields for compatibility
    role: Optional[str] = None
    use_cases: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1


@dataclass
class AgentSelection:
    """Selected agents for a project."""

    core_agents: List[AgentInfo] = field(default_factory=list)
    domain_agents: List[AgentInfo] = field(default_factory=list)
    workflow_agents: List[AgentInfo] = field(default_factory=list)
    custom_agents: List[AgentInfo] = field(default_factory=list)
    agent_priorities: Dict[str, int] = field(default_factory=dict)
    coordination_patterns: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def all_agents(self) -> List[AgentInfo]:
        """Get all agents combined."""
        return (
            self.core_agents
            + self.domain_agents
            + self.workflow_agents
            + self.custom_agents
        )


@dataclass
class GeneratedContent:
    """Content generated by template system."""

    files: Dict[str, str] = field(default_factory=dict)  # filename -> content
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent_selection: Optional[AgentSelection] = None
    template_info: Dict[str, str] = field(default_factory=dict)
    generation_timestamp: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validation operations."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class TemplateRequest(BaseModel):
    """Request for template generation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    analysis: ProjectAnalysis
    template_name: Optional[str] = None
    output_format: str = "files"
    customizations: Dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    """Result of main execution."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool
    analysis: Optional[ProjectAnalysis] = None
    generated_content: Optional[GeneratedContent] = None
    git_integration_result: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    execution_time: Optional[float] = None


# Test-compatible FrameworkInfo (different from the main FrameworkInfo)
@dataclass
class TestFrameworkInfo:
    """Test-compatible framework information model."""

    name: str
    version: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "category": self.category,
            "description": self.description,
        }


# Note: TestFrameworkInfo is available for specific model tests
# CLI tests should use the real FrameworkInfo from this module


# Placeholder classes for test compatibility
@dataclass
class AnalysisResult:
    """Analysis result model for test compatibility."""

    project_info: Optional[Union["ProjectInfo", Dict[str, Any]]] = None
    frameworks: List[Union["TestFrameworkInfo", Dict[str, Any]]] = field(
        default_factory=list
    )
    dependencies: List[Union["DependencyInfo", Dict[str, Any]]] = field(
        default_factory=list
    )
    file_structure: Optional[Union["FileStructure", Dict[str, Any]]] = None
    analysis_timestamp: Optional[Any] = None
    success: bool = True
    confidence: float = 0.8
    project_type: Optional[ProjectType] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    complexity: Optional[ComplexityLevel] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Process nested dictionaries into proper objects."""
        # Auto-generate timestamp if not provided
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.now(tz=timezone.utc)

        # Normalize project_info from dict
        if isinstance(self.project_info, dict):
            pi = self.project_info
            self.project_info = ProjectInfo(
                name=pi.get("name", "unknown"),
                project_type=pi.get("project_type"),
                framework=pi.get("framework"),
                description=pi.get("description"),
                version=pi.get("version"),
                language_version=pi.get("language_version"),
                main_directory=pi.get("main_directory"),
                path=pi.get("path", "."),
                language=pi.get("language"),
                dependencies=pi.get("dependencies", []),
            )

        # Normalize frameworks from dicts
        normalized_frameworks: List[TestFrameworkInfo] = []
        for f in self.frameworks:
            if isinstance(f, dict):
                normalized_frameworks.append(
                    TestFrameworkInfo(
                        name=f.get("name", "unknown"),
                        version=f.get("version"),
                        category=f.get("category"),
                        description=f.get("description"),
                    )
                )
            else:
                normalized_frameworks.append(f)
        self.frameworks = normalized_frameworks  # type: ignore[assignment]

        # Normalize dependencies from dicts
        normalized_deps: List[DependencyInfo] = []
        for d in self.dependencies:
            if isinstance(d, dict):
                normalized_deps.append(
                    DependencyInfo(
                        name=d.get("name", "unknown"),
                        version=d.get("version"),
                        dependency_type=d.get("dependency_type", "runtime"),
                        source=d.get("source"),
                    )
                )
            else:
                normalized_deps.append(d)
        self.dependencies = normalized_deps  # type: ignore[assignment]

        # Normalize file_structure
        if isinstance(self.file_structure, dict):
            fs = self.file_structure
            self.file_structure = FileStructure(
                path=fs.get("path", "."),
                file_type=fs.get("file_type", "file"),
                size=fs.get("size"),
                language=fs.get("language"),
                children=fs.get("children", []),
                source_files=fs.get("source_files", []),
                test_files=fs.get("test_files", []),
                config_files=fs.get("config_files", []),
                documentation_files=fs.get("documentation_files", []),
            )

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "project_info": (
                self.project_info.dict()
                if self.project_info and hasattr(self.project_info, "dict")
                else None
            ),
            "frameworks": [
                f.dict() if hasattr(f, "dict") else f for f in self.frameworks
            ],
            "dependencies": [
                d.dict() if hasattr(d, "dict") else d for d in self.dependencies
            ],
            "file_structure": (
                self.file_structure.dict()
                if self.file_structure and hasattr(self.file_structure, "dict")
                else None
            ),
            "analysis_timestamp": (
                str(self.analysis_timestamp) if self.analysis_timestamp else None
            ),
            "success": self.success,
            "confidence": self.confidence,
            "project_type": self.project_type.value if self.project_type else None,
            "language": self.language,
            "framework": self.framework,
            "complexity": self.complexity.value if self.complexity else None,
            "errors": self.errors,
            "metadata": self.metadata,
        }

    def filter_dependencies(self, dependency_type: str) -> List["DependencyInfo"]:
        """Filter dependencies by type."""
        from typing import cast

        return cast(
            "List[DependencyInfo]",
            [
                d
                for d in self.dependencies
                if hasattr(d, "dependency_type")
                and d.dependency_type == dependency_type
            ],
        )


@dataclass
class DependencyInfo:
    """Dependency information model for test compatibility."""

    name: str
    version: Optional[str] = None
    dependency_type: str = "runtime"
    source: Optional[str] = None
    package_managers: List[str] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    dev_dependencies: Dict[str, str] = field(default_factory=dict)

    VALID_DEPENDENCY_TYPES = {"runtime", "development", "test", "build", "optional"}

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError(DEPENDENCY_NAME_CANNOT_BE_EMPTY)

        if self.dependency_type not in self.VALID_DEPENDENCY_TYPES:
            msg = (
                f"{INVALID_DEPENDENCY_TYPE}: {self.dependency_type}. "
                f"Valid types: {', '.join(self.VALID_DEPENDENCY_TYPES)}"
            )
            raise ValueError(msg)

    def is_dev_dependency(self) -> bool:
        """Check if this is a development dependency."""
        return self.dependency_type in {"development", "test"}

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "dependency_type": self.dependency_type,
            "source": self.source,
            "package_managers": self.package_managers,
            "dependencies": self.dependencies,
            "dev_dependencies": self.dev_dependencies,
        }


@dataclass
class FileStructure:
    """File structure information model for test compatibility."""

    path: str
    file_type: str = "file"
    size: Optional[int] = None
    language: Optional[str] = None
    children: List[str] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)
    test_files: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    documentation_files: List[str] = field(default_factory=list)

    VALID_FILE_TYPES = {"file", "directory", "symlink"}

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if not self.path:
            raise ValueError(PATH_CANNOT_BE_EMPTY)

        if self.file_type not in self.VALID_FILE_TYPES:
            msg = (
                f"{INVALID_FILE_TYPE}: {self.file_type}. "
                f"Valid types: {', '.join(self.VALID_FILE_TYPES)}"
            )
            raise ValueError(msg)

    def is_directory(self) -> bool:
        """Check if this represents a directory."""
        return self.file_type == "directory"

    def is_file(self) -> bool:
        """Check if this represents a file."""
        return self.file_type == "file"

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path": self.path,
            "file_type": self.file_type,
            "size": self.size,
            "language": self.language,
            "children": self.children,
            "source_files": self.source_files,
            "test_files": self.test_files,
            "config_files": self.config_files,
            "documentation_files": self.documentation_files,
        }


@dataclass
class GenerationConfig:
    """Generation configuration model for test compatibility."""

    output_format: str = "markdown"
    include_agents: bool = True
    include_workflow: bool = True
    template_variant: str = "comprehensive"
    create_zip: bool = False
    output_directory: Optional[str] = None
    template_name: str = "default"
    output_path: str = "."
    variables: Dict[str, str] = field(default_factory=dict)
    overwrite_existing: bool = False

    VALID_OUTPUT_FORMATS = {"markdown", "html", "json", "yaml"}
    VALID_TEMPLATE_VARIANTS = {"comprehensive", "minimal", "basic", "advanced"}

    def validate(self) -> None:
        """Validate the configuration."""
        if self.output_format not in self.VALID_OUTPUT_FORMATS:
            msg = (
                f"{INVALID_OUTPUT_FORMAT}: {self.output_format}. "
                f"Valid formats: {', '.join(self.VALID_OUTPUT_FORMATS)}"
            )
            raise ValueError(msg)

        if self.template_variant not in self.VALID_TEMPLATE_VARIANTS:
            msg = (
                f"{INVALID_TEMPLATE_VARIANT}: {self.template_variant}. "
                f"Valid variants: {', '.join(self.VALID_TEMPLATE_VARIANTS)}"
            )
            raise ValueError(msg)

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "output_format": self.output_format,
            "include_agents": self.include_agents,
            "include_workflow": self.include_workflow,
            "template_variant": self.template_variant,
            "create_zip": self.create_zip,
            "output_directory": self.output_directory,
            "template_name": self.template_name,
            "output_path": self.output_path,
            "variables": self.variables,
            "overwrite_existing": self.overwrite_existing,
        }


@dataclass
class ProjectInfo:
    """Project information model for test compatibility."""

    name: str
    project_type: Optional[str] = None
    framework: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    language_version: Optional[str] = None
    main_directory: Optional[str] = None
    path: str = "."
    language: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

    VALID_PROJECT_TYPES = {
        "python",
        "rust",
        "javascript",
        "java",
        "go",
        "cpp",
        "csharp",
        "php",
        "unknown",
    }

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError(PROJECT_NAME_CANNOT_BE_EMPTY)

        if self.project_type and self.project_type not in self.VALID_PROJECT_TYPES:
            msg = (
                f"{INVALID_PROJECT_TYPE}: {self.project_type}. "
                f"Valid types: {', '.join(self.VALID_PROJECT_TYPES)}"
            )
            raise ValueError(msg)

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "project_type": self.project_type,
            "framework": self.framework,
            "description": self.description,
            "version": self.version,
            "language_version": self.language_version,
            "main_directory": self.main_directory,
            "path": self.path,
            "language": self.language,
            "dependencies": self.dependencies,
        }


class OutputTarget(Enum):
    """Supported output targets for generated agent instructions."""

    CLAUDE = "claude"
    CODEX = "codex"
    GEMINI = "gemini"


@dataclass
class GeneratedArtifact:
    """A generated file artifact with relative path and content."""

    path: str
    content: str
    description: str = ""

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if not self.path or not self.path.strip():
            msg = "Artifact path cannot be empty"
            raise ValueError(msg)

    @property
    def size_bytes(self) -> int:
        """Return artifact content size in bytes."""
        return len(self.content.encode("utf-8"))


@dataclass
class RenderedTargetOutput:
    """Rendered artifacts for a specific output target."""

    target: OutputTarget
    artifacts: List[GeneratedArtifact]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_files(self) -> int:
        """Total number of artifacts in this output."""
        return len(self.artifacts)

    def get_paths(self) -> List[str]:
        """Return artifact paths in render order."""
        return [artifact.path for artifact in self.artifacts]


# New data classes for YAML subagent architecture
@dataclass
class SubagentFile:
    """Individual subagent file with YAML front matter."""

    name: str
    content: str  # Includes YAML front matter + system prompt
    path: str  # Relative path like .claude/agents/agent-name.md

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if not self.name or not self.name.strip():
            msg = "Subagent name cannot be empty"
            raise ValueError(msg)
        if not self.content:
            msg = "Subagent content cannot be empty"
            raise ValueError(msg)
        if not self.path:
            msg = "Subagent path cannot be empty"
            raise ValueError(msg)


@dataclass
class EnvironmentBundle:
    """Complete development environment bundle."""

    claude_md: str  # Project documentation content
    subagent_files: List[SubagentFile]  # Individual agent files with YAML
    agents_md: str  # User guide content
    metadata: Dict[str, Any] = field(default_factory=dict)
    generation_timestamp: Optional[str] = None

    @property
    def total_files(self) -> int:
        """Total number of files in the bundle."""
        return len(self.subagent_files) + 2  # +2 for CLAUDE.md and AGENTS.md

    def get_all_file_paths(self) -> List[str]:
        """Get all file paths that will be generated."""
        paths = ["CLAUDE.md", "AGENTS.md"]
        paths.extend([sf.path for sf in self.subagent_files])
        return paths


@dataclass
class AgentDefinition:
    """Enhanced agent definition for YAML front matter generation."""

    name: str
    description: str
    tools: List[str]
    system_prompt: str
    specialization: str
    category: str = "general"
    confidence: float = 1.0
    project_context: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if not self.name or not self.name.strip():
            msg = "Agent name cannot be empty"
            raise ValueError(msg)
        if not self.description:
            msg = "Agent description cannot be empty"
            raise ValueError(msg)
        if not self.tools:
            msg = "Agent tools cannot be empty"
            raise ValueError(msg)
        if not self.system_prompt:
            msg = "Agent system prompt cannot be empty"
            raise ValueError(msg)

    @property
    def yaml_name(self) -> str:
        """Generate proper agent name for YAML (kebab-case)."""
        return self.name.lower().replace("_", "-").replace(" ", "-")

    def get_yaml_tools(self) -> str:
        """Format tools for YAML front matter."""
        return ", ".join(self.tools)
