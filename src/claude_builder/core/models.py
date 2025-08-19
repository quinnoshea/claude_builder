"""Data models for Claude Builder."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectType(Enum):
    """Detected project types."""
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    DATA_SCIENCE = "data_science"
    MICROSERVICE = "microservice"
    MONOREPO = "monorepo"
    DESKTOP_APP = "desktop_app"
    MOBILE_APP = "mobile_app"
    GAME = "game"
    UNKNOWN = "unknown"


class ComplexityLevel(Enum):
    """Project complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
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


@dataclass
class FrameworkInfo:
    """Information about detected frameworks."""
    primary: Optional[str] = None
    secondary: List[str] = field(default_factory=list)
    confidence: float = 0.0
    version: Optional[str] = None
    config_files: List[str] = field(default_factory=list)


@dataclass
class DomainInfo:
    """Information about application domain."""
    domain: Optional[str] = None
    confidence: float = 0.0
    indicators: List[str] = field(default_factory=list)
    specialized_patterns: List[str] = field(default_factory=list)


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
    dev_environment: DevelopmentEnvironment = field(default_factory=DevelopmentEnvironment)
    filesystem_info: FileSystemInfo = field(default_factory=FileSystemInfo)

    # Analysis metadata
    analysis_confidence: float = 0.0
    analysis_timestamp: Optional[str] = None
    analyzer_version: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

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
        return self.project_type in [ProjectType.WEB_APPLICATION, ProjectType.API_SERVICE]

    @property
    def is_cli_project(self) -> bool:
        """Check if this is a CLI tool project."""
        return self.project_type == ProjectType.CLI_TOOL

    @property
    def uses_database(self) -> bool:
        """Check if project uses a database."""
        return len(self.dev_environment.databases) > 0

    @property
    def has_tests(self) -> bool:
        """Check if project has testing setup."""
        return len(self.dev_environment.testing_frameworks) > 0 or self.filesystem_info.test_files > 0

    @property
    def has_ci_cd(self) -> bool:
        """Check if project has CI/CD setup."""
        return len(self.dev_environment.ci_cd_systems) > 0

    @property
    def is_containerized(self) -> bool:
        """Check if project uses containerization."""
        return len(self.dev_environment.containerization) > 0


class ClaudeMentionPolicy(Enum):
    """Policies for Claude mentions in generated content."""
    ALLOWED = "allowed"      # Full Claude attribution
    MINIMAL = "minimal"      # Minimal references, only in dev docs
    FORBIDDEN = "forbidden"  # No Claude references anywhere


class GitIntegrationMode(Enum):
    """Git integration modes."""
    NO_INTEGRATION = "no_integration"
    EXCLUDE_GENERATED = "exclude_generated"
    TRACK_GENERATED = "track_generated"


@dataclass
class AgentSelection:
    """Selected agents for a project."""
    core_agents: List[str] = field(default_factory=list)
    specialized_agents: List[str] = field(default_factory=list)
    workflow_agents: List[str] = field(default_factory=list)
    custom_agents: List[str] = field(default_factory=list)
    agent_priorities: Dict[str, int] = field(default_factory=dict)
    coordination_patterns: Dict[str, List[str]] = field(default_factory=dict)


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
    analysis: ProjectAnalysis
    template_name: Optional[str] = None
    output_format: str = "files"
    customizations: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class ExecutionResult(BaseModel):
    """Result of main execution."""
    success: bool
    analysis: Optional[ProjectAnalysis] = None
    generated_content: Optional[GeneratedContent] = None
    git_integration_result: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    execution_time: Optional[float] = None

    class Config:
        arbitrary_types_allowed = True


# Placeholder classes for test compatibility
@dataclass 
class AnalysisResult:
    """Placeholder AnalysisResult class for test compatibility."""
    success: bool = True
    confidence: float = 0.8
    project_type: Optional[ProjectType] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    complexity: Optional[ComplexityLevel] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyInfo:
    """Placeholder DependencyInfo class for test compatibility."""
    package_managers: List[str] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    dev_dependencies: Dict[str, str] = field(default_factory=dict)


@dataclass
class FileStructure:
    """Placeholder FileStructure class for test compatibility."""
    source_files: List[str] = field(default_factory=list)
    test_files: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    documentation_files: List[str] = field(default_factory=list)


@dataclass
class GenerationConfig:
    """Placeholder GenerationConfig class for test compatibility."""
    template_name: str = "default"
    output_path: str = "."
    variables: Dict[str, str] = field(default_factory=dict)
    overwrite_existing: bool = False


@dataclass
class ProjectInfo:
    """Placeholder ProjectInfo class for test compatibility."""
    name: str = "unknown"
    path: str = "."
    language: str = "unknown"
    framework: str = "none"
    dependencies: List[str] = field(default_factory=list)
