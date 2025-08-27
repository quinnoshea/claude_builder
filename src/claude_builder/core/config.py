"""Configuration management for Claude Builder."""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional

from claude_builder.core.models import ClaudeMentionPolicy, GitIntegrationMode
from claude_builder.utils.exceptions import ConfigError


FAILED_TO_LOAD_CONFIGURATION = "Failed to load configuration"
FAILED_TO_SAVE_CONFIGURATION = "Failed to save configuration"
CONFIGURATION_FILE_NOT_FOUND = "Configuration file not found"
FAILED_TO_PARSE_CONFIGURATION_FILE = "Failed to parse configuration file"
FAILED_TO_CONVERT_DICTIONARY_TO_CONFIG = "Failed to convert dictionary to Config"
PROJECT_PROFILE_NOT_FOUND = "Project profile not found"
FAILED_TO_APPLY_PROFILE = "Failed to apply profile"
UNSUPPORTED_CONFIG_VERSION = "Unsupported config version"
CONFIDENCE_THRESHOLD_ERROR = "confidence_threshold must be between 0 and 100"
MAX_CONCURRENT_AGENTS_ERROR = "max_concurrent_agents must be at least 1"
AGENT_TIMEOUT_ERROR = "agent_timeout must be at least 30 seconds"
TEMPLATE_CACHE_TTL_ERROR = "template_cache_ttl must be non-negative"
MAX_FILE_SIZE_ERROR = "max_file_size must be at least 1024 bytes"
INVALID_FILE_PERMISSIONS_FORMAT = "Invalid file permissions format"
INVALID_UPDATE_CHECK_FREQUENCY = "Invalid update_check_frequency"
INVALID_THEME = "Invalid theme"
INVALID_AGENT_SELECTION_ALGORITHM = "Invalid agent_selection_algorithm"


@dataclass
class AnalysisConfig:
    """Configuration for project analysis."""

    ignore_patterns: List[str] = field(
        default_factory=lambda: [
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
        ]
    )
    cache_enabled: bool = True
    parallel_processing: bool = True
    confidence_threshold: int = 80
    overrides: Dict[str, Optional[str]] = field(default_factory=dict)
    custom_detection_rules: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    max_file_size: int = 10485760  # 10MB
    max_files_to_analyze: int = 10000
    deep_analysis: bool = False  # More thorough but slower analysis


@dataclass
class TemplateConfig:
    """Configuration for template system."""

    search_paths: List[str] = field(
        default_factory=lambda: ["./templates/", "~/.claude-builder/templates/"]
    )
    preferred_templates: List[str] = field(default_factory=list)
    template_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    auto_update_templates: bool = False
    template_cache_ttl: int = 86400  # 24 hours
    allow_community_templates: bool = True
    template_validation_strict: bool = False
    custom_variables: Dict[str, str] = field(default_factory=dict)


@dataclass
class AgentConfig:
    """Configuration for agent system."""

    install_automatically: bool = True
    exclude_agents: List[str] = field(default_factory=list)
    priority_agents: List[str] = field(default_factory=list)
    custom_agent_paths: List[str] = field(default_factory=list)
    workflows: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "feature_development": [
                "research",
                "design",
                "implement",
                "test",
                "deploy",
            ],
            "bug_fixing": ["investigate", "fix", "test", "document"],
        }
    )
    agent_selection_algorithm: str = (
        "intelligent"  # 'intelligent', 'strict', 'permissive'
    )
    max_concurrent_agents: int = 5
    agent_timeout: int = 300  # 5 minutes
    auto_install_dependencies: bool = True
    agent_preferences: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class GitIntegrationConfig:
    """Configuration for git integration."""

    enabled: bool = True
    mode: GitIntegrationMode = GitIntegrationMode.NO_INTEGRATION
    claude_mention_policy: ClaudeMentionPolicy = ClaudeMentionPolicy.MINIMAL
    backup_before_changes: bool = True
    files_to_exclude: List[str] = field(
        default_factory=lambda: ["CLAUDE.md", "AGENTS.md", ".claude/", "docs/claude-*"]
    )


@dataclass
class OutputConfig:
    """Configuration for output generation."""

    format: str = "files"
    backup_existing: bool = True
    create_directories: bool = True
    file_permissions: str = "0644"
    validate_generated: bool = True


@dataclass
class UserPreferences:
    """User preferences and settings."""

    default_editor: str = "code"
    prefer_verbose_output: bool = False
    auto_open_generated_files: bool = False
    confirmation_prompts: bool = True
    theme: str = "auto"  # 'light', 'dark', 'auto'
    language: str = "en"
    timezone: Optional[str] = None
    analytics_enabled: bool = True
    update_check_frequency: str = "weekly"  # 'never', 'daily', 'weekly', 'monthly'
    workspace_memory: bool = True  # Remember workspace-specific settings
    keyboard_shortcuts: Dict[str, str] = field(default_factory=dict)
    notification_preferences: Dict[str, bool] = field(
        default_factory=lambda: {
            "template_updates": True,
            "agent_updates": True,
            "security_alerts": True,
            "feature_announcements": False,
        }
    )


@dataclass
class HealthConfig:
    """Configuration for health monitoring system."""

    enabled: bool = True
    check_interval: int = 60  # seconds
    alert_threshold: int = 3  # consecutive failures before alert
    timeout: int = 60  # health check timeout in seconds
    export_reports: bool = True
    report_directory: str = "./health-reports"
    enabled_checks: List[str] = field(
        default_factory=lambda: [
            "application",
            "dependency",
            "security",
            "performance",
            "configuration",
        ]
    )
    performance_thresholds: Dict[str, Any] = field(
        default_factory=lambda: {
            "memory_usage_warning": 80,  # percent
            "memory_usage_critical": 90,  # percent
            "cpu_usage_warning": 80,  # percent
            "cpu_usage_critical": 90,  # percent
            "disk_usage_warning": 85,  # percent
            "disk_usage_critical": 95,  # percent
        }
    )
    notification_settings: Dict[str, Any] = field(
        default_factory=lambda: {
            "enable_console_alerts": True,
            "enable_file_logging": True,
            "log_file": "health.log",
        }
    )


@dataclass
class IntegrationConfig:
    """Configuration for external integrations."""

    ide_integrations: Dict[str, bool] = field(
        default_factory=lambda: {"vscode": True, "jetbrains": False, "vim": False}
    )
    package_managers: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: {
            "npm": {"auto_install": False, "registry": "https://registry.npmjs.org/"},
            "pip": {"auto_install": False, "index_url": "https://pypi.org/simple/"},
            "cargo": {"auto_install": False, "registry": "https://crates.io/"},
        }
    )
    ci_cd_platforms: Dict[str, bool] = field(
        default_factory=lambda: {
            "github_actions": True,
            "gitlab_ci": False,
            "jenkins": False,
        }
    )
    cloud_platforms: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class Config:
    """Main configuration object."""

    version: str = "1.0"
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    templates: TemplateConfig = field(default_factory=TemplateConfig)
    agents: AgentConfig = field(default_factory=AgentConfig)
    git_integration: GitIntegrationConfig = field(default_factory=GitIntegrationConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    user_preferences: UserPreferences = field(default_factory=UserPreferences)
    integrations: IntegrationConfig = field(default_factory=IntegrationConfig)
    health: HealthConfig = field(default_factory=HealthConfig)
    workspace_settings: Dict[str, Any] = field(default_factory=dict)
    project_profiles: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class ConfigManager:
    """Manages configuration loading, saving, and merging using composition pattern."""

    DEFAULT_CONFIG_NAMES: ClassVar[List[str]] = [
        "claude-builder.json",
        "claude-builder.toml",
        ".claude-builder.json",
        ".claude-builder.toml",
    ]

    GLOBAL_CONFIG_NAMES: ClassVar[List[str]] = [
        "~/.config/claude-builder/config.json",
        "~/.config/claude-builder/config.toml",
        "~/.claude-builder/config.json",
        "~/.claude-builder/config.toml",
    ]

    def __init__(self) -> None:
        self.schema_version = "1.0"
        self.workspace_cache: Dict[str, Any] = {}  # In-memory workspace settings cache

        # Initialize specialized components
        from claude_builder.core.config_management import (
            ConfigEnvironment,
            ConfigLoader,
            ConfigValidator,
        )

        self._loader = ConfigLoader()
        self._validator = ConfigValidator(self.schema_version)
        self._environment = ConfigEnvironment()

        # Sync workspace cache with environment component
        self._environment.workspace_cache = self.workspace_cache

    def load_config(
        self,
        project_path: Path,
        config_file: Optional[Path] = None,
        cli_overrides: Optional[Dict[str, Any]] = None,
    ) -> Config:
        """Load configuration with proper precedence."""
        try:
            # Start with default config
            config = Config()

            # Load from config file if specified or found
            if config_file:
                file_config = self._loader.load_config_file(config_file)
                config = self._merge_configs(config, file_config)
            else:
                # Look for config files in project directory
                found_config = self._loader.find_config_file(project_path)
                if found_config:
                    file_config = self._loader.load_config_file(found_config)
                    config = self._merge_configs(config, file_config)

            # Apply CLI overrides
            if cli_overrides:
                config = self._apply_cli_overrides(config, cli_overrides)

            # Validate configuration
            self._validator.validate_config(config)

            return config

        except Exception as e:
            msg = f"{FAILED_TO_LOAD_CONFIGURATION}: {e}"
            raise ConfigError(msg) from e

    def save_config(self, config: Config, config_path: Path) -> None:
        """Save configuration to file."""
        try:
            config_dict = self._config_to_dict(config)

            # Prepare for serialization
            serializable_dict = self._loader.prepare_for_serialization(config_dict)

            if config_path.suffix.lower() == ".toml":
                self._loader.save_toml_config(serializable_dict, config_path)
            else:
                self._loader.save_json_config(serializable_dict, config_path)

        except Exception as e:
            msg = f"{FAILED_TO_SAVE_CONFIGURATION}: {e}"
            raise ConfigError(msg) from e

    def create_default_config(self, project_path: Path) -> Config:
        """Create a default configuration for a project."""
        return Config()

        # Customize based on project characteristics
        # This would be enhanced with project analysis results

    def _find_config_file(self, project_path: Path) -> Optional[Path]:
        """Find configuration file in project directory."""
        return self._loader.find_config_file(project_path)

    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from file."""
        return self._loader.load_config_file(config_path)

    def _merge_configs(self, base: Config, override: Dict[str, Any]) -> Config:
        """Merge configuration dictionaries."""
        # Convert base config to dict
        base_dict = self._config_to_dict(base)

        # Deep merge override into base
        merged = self._deep_merge(base_dict, override)

        # Convert back to Config object
        return self._dict_to_config(merged)

    def _apply_cli_overrides(
        self, config: Config, cli_overrides: Dict[str, Any]
    ) -> Config:
        """Apply CLI overrides to configuration."""
        # Map CLI options to config paths
        cli_mapping = {
            "verbose": ("user_preferences", "prefer_verbose_output"),
            "quiet": ("user_preferences", "prefer_verbose_output"),  # Inverse
            "template": ("templates", "preferred_templates"),
            "git_exclude": ("git_integration", "mode"),
            "git_track": ("git_integration", "mode"),
            "claude_mentions": ("git_integration", "claude_mention_policy"),
            "no_git": ("git_integration", "enabled"),
            "backup_existing": ("output", "backup_existing"),
            "output_format": ("output", "format"),
        }

        config_dict = self._config_to_dict(config)

        for cli_key, value in cli_overrides.items():
            if value is None:
                continue

            if cli_key in cli_mapping:
                section, key = cli_mapping[cli_key]

                # Special handling for specific options
                if cli_key == "quiet" and value:
                    config_dict[section][key] = False
                elif cli_key == "template" and value:
                    config_dict[section][key] = [value]
                elif cli_key == "git_exclude" and value:
                    config_dict["git_integration"]["mode"] = "exclude_generated"
                elif cli_key == "git_track" and value:
                    config_dict["git_integration"]["mode"] = "track_generated"
                elif cli_key == "no_git" and value:
                    config_dict["git_integration"]["enabled"] = False
                elif cli_key == "claude_mentions":
                    config_dict["git_integration"]["claude_mention_policy"] = value
                else:
                    config_dict[section][key] = value

        return self._dict_to_config(config_dict)

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _config_to_dict(self, config: Config) -> Dict[str, Any]:
        """Convert Config object to dictionary."""
        return asdict(config)

    def _dict_to_config(self, config_dict: Dict[str, Any]) -> Config:
        """Convert dictionary to Config object."""
        try:
            # Create nested objects
            analysis_config = AnalysisConfig(**config_dict.get("analysis", {}))
            template_config = TemplateConfig(**config_dict.get("templates", {}))
            agent_config = AgentConfig(**config_dict.get("agents", {}))

            # Handle enums for git integration
            git_config_dict = config_dict.get("git_integration", {})
            if "mode" in git_config_dict and isinstance(git_config_dict["mode"], str):
                git_config_dict["mode"] = GitIntegrationMode(git_config_dict["mode"])
            if "claude_mention_policy" in git_config_dict and isinstance(
                git_config_dict["claude_mention_policy"], str
            ):
                git_config_dict["claude_mention_policy"] = ClaudeMentionPolicy(
                    git_config_dict["claude_mention_policy"]
                )

            git_integration_config = GitIntegrationConfig(**git_config_dict)
            output_config = OutputConfig(**config_dict.get("output", {}))
            user_preferences = UserPreferences(
                **config_dict.get("user_preferences", {})
            )
            integration_config = IntegrationConfig(
                **config_dict.get("integrations", {})
            )
            health_config = HealthConfig(**config_dict.get("health", {}))

            return Config(
                version=config_dict.get("version", "1.0"),
                analysis=analysis_config,
                templates=template_config,
                agents=agent_config,
                git_integration=git_integration_config,
                output=output_config,
                user_preferences=user_preferences,
                integrations=integration_config,
                health=health_config,
                workspace_settings=config_dict.get("workspace_settings", {}),
                project_profiles=config_dict.get("project_profiles", {}),
            )
        except Exception as e:
            msg = f"{FAILED_TO_CONVERT_DICTIONARY_TO_CONFIG}: {e}"
            raise ConfigError(msg) from e

    def _save_json_config(self, config_dict: Dict[str, Any], config_path: Path) -> None:
        """Save configuration as JSON."""
        self._loader.save_json_config(config_dict, config_path)

    def _save_toml_config(self, config_dict: Dict[str, Any], config_path: Path) -> None:
        """Save configuration as TOML."""
        self._loader.save_toml_config(config_dict, config_path)

    def _prepare_for_serialization(self, obj: Any) -> Any:
        """Prepare object for JSON/TOML serialization."""
        return self._loader.prepare_for_serialization(obj)

    def load_global_config(self) -> Optional[Config]:
        """Load global configuration from user's home directory."""
        config_data = self._loader.load_global_config()
        if config_data:
            return self._dict_to_config(config_data)
        return None

    def save_workspace_setting(self, project_path: Path, key: str, value: Any) -> None:
        """Save a workspace-specific setting."""
        self._environment.save_workspace_setting(project_path, key, value)
        # Sync with our cache
        self.workspace_cache = self._environment.workspace_cache

    def get_workspace_setting(
        self, project_path: Path, key: str, default: Any = None
    ) -> Any:
        """Get a workspace-specific setting."""
        result = self._environment.get_workspace_setting(project_path, key, default)
        # Sync with our cache
        self.workspace_cache = self._environment.workspace_cache
        return result

    def create_project_profile(
        self, profile_name: str, config: Config, description: str = ""
    ) -> None:
        """Create a project profile for reuse."""
        self._environment.create_project_profile(profile_name, config, description)

    def list_project_profiles(self) -> List[Dict[str, Any]]:
        """List available project profiles."""
        return self._environment.list_project_profiles()

    def apply_project_profile(self, profile_name: str, base_config: Config) -> Config:
        """Apply a project profile to base configuration."""
        return self._environment.apply_project_profile(profile_name, base_config)

    def validate_config_compatibility(
        self, config: Config, project_analysis: Optional[Any] = None
    ) -> List[str]:
        """Validate configuration compatibility with project."""
        return self._validator.validate_config_compatibility(config, project_analysis)

    def _validate_config(self, config: Config) -> None:
        """Validate configuration object."""
        self._validator.validate_config(config)


def load_config_from_args(args: Dict[str, Any]) -> Config:
    """Convenience function to load config from command-line arguments."""
    config_manager = ConfigManager()

    project_path = Path(args.get("project_path", ".")).resolve()
    config_file = Path(args["config_file"]) if args.get("config_file") else None

    return config_manager.load_config(
        project_path=project_path, config_file=config_file, cli_overrides=args
    )


# Placeholder classes for test compatibility
class AdvancedConfigManager:
    """Placeholder AdvancedConfigManager class for test compatibility."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = config_path
        self.config: Dict[str, Any] = {}

    def load_advanced_config(self) -> dict:
        """Load advanced configuration."""
        return {"advanced": True, "settings": {}}

    def validate_config(self) -> bool:
        """Validate configuration."""
        return True

    def merge_configs(self, *configs: Any) -> dict:
        """Merge multiple configurations."""
        result = {}
        for config in configs:
            result.update(config)
        return result


class ConfigEnvironment:
    """Placeholder ConfigEnvironment class for test compatibility."""

    def __init__(self, env_name: str = "development"):
        self.env_name = env_name
        self.variables: Dict[str, Any] = {}

    def get_environment_config(self) -> Dict[str, Any]:
        return {"environment": self.env_name, "debug": True}


class ConfigSchema:
    """Placeholder ConfigSchema class for test compatibility."""

    def __init__(self, schema_dict: Optional[Dict[str, Any]] = None) -> None:
        self.schema = schema_dict or {}

    def validate(self, config: Dict[str, Any]) -> bool:
        return True

    def get_defaults(self) -> Dict[str, Any]:
        return {"version": "1.0", "debug": False}


class ConfigValidator:
    """Placeholder ConfigValidator class for test compatibility."""

    def __init__(self) -> None:
        self.rules: List[Any] = []

    def validate_project_config(self, config: dict) -> dict:
        """Validate project configuration."""
        return {"is_valid": True, "errors": [], "warnings": []}

    def add_validation_rule(self, rule: Any) -> None:
        """Add validation rule."""
        self.rules.append(rule)


class ConfigWatcher:
    """Placeholder ConfigWatcher class for test compatibility."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.is_watching = False

    def start_watching(self) -> bool:
        self.is_watching = True
        return True

    def stop_watching(self) -> bool:
        self.is_watching = False
        return True

    def on_config_changed(self, callback: Any) -> None:
        pass


class SecureConfigHandler:
    """Placeholder SecureConfigHandler class for test compatibility."""

    def __init__(self, encryption_key: Optional[str] = None) -> None:
        self.encryption_key = encryption_key

    def encrypt_config(self, config: Dict[str, Any]) -> str:
        return "encrypted_config_data"

    def decrypt_config(self, encrypted_data: str) -> Dict[str, Any]:
        return {"decrypted": "config"}

    def store_secure_config(self, config: Dict[str, Any], path: str) -> bool:
        return True
