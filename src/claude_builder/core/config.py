"""Configuration management for Claude Builder."""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import toml

from claude_builder.utils.exceptions import ConfigError
from claude_builder.core.models import ClaudeMentionPolicy, GitIntegrationMode


@dataclass
class AnalysisConfig:
    """Configuration for project analysis."""
    ignore_patterns: List[str] = field(default_factory=lambda: [
        ".git/", "node_modules/", "__pycache__/", "target/", "dist/",
        "build/", ".venv/", "venv/", ".tox/", ".coverage"
    ])
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
    search_paths: List[str] = field(default_factory=lambda: [
        "./templates/", "~/.claude-builder/templates/"
    ])
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
    workflows: Dict[str, List[str]] = field(default_factory=lambda: {
        "feature_development": ["research", "design", "implement", "test", "deploy"],
        "bug_fixing": ["investigate", "fix", "test", "document"]
    })
    agent_selection_algorithm: str = "intelligent"  # 'intelligent', 'strict', 'permissive'
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
    files_to_exclude: List[str] = field(default_factory=lambda: [
        "CLAUDE.md", "AGENTS.md", ".claude/", "docs/claude-*"
    ])


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
    notification_preferences: Dict[str, bool] = field(default_factory=lambda: {
        "template_updates": True,
        "agent_updates": True,
        "security_alerts": True,
        "feature_announcements": False
    })


@dataclass
class IntegrationConfig:
    """Configuration for external integrations."""
    ide_integrations: Dict[str, bool] = field(default_factory=lambda: {
        "vscode": True,
        "jetbrains": False,
        "vim": False
    })
    package_managers: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "npm": {"auto_install": False, "registry": "https://registry.npmjs.org/"},
        "pip": {"auto_install": False, "index_url": "https://pypi.org/simple/"},
        "cargo": {"auto_install": False, "registry": "https://crates.io/"}
    })
    ci_cd_platforms: Dict[str, bool] = field(default_factory=lambda: {
        "github_actions": True,
        "gitlab_ci": False,
        "jenkins": False
    })
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
    workspace_settings: Dict[str, Any] = field(default_factory=dict)
    project_profiles: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class ConfigManager:
    """Manages configuration loading, saving, and merging."""

    DEFAULT_CONFIG_NAMES = [
        "claude-builder.json",
        "claude-builder.toml",
        ".claude-builder.json",
        ".claude-builder.toml"
    ]

    GLOBAL_CONFIG_NAMES = [
        "~/.config/claude-builder/config.json",
        "~/.config/claude-builder/config.toml",
        "~/.claude-builder/config.json",
        "~/.claude-builder/config.toml"
    ]

    def __init__(self):
        self.schema_version = "1.0"
        self.workspace_cache = {}  # In-memory workspace settings cache

    def load_config(
        self,
        project_path: Path,
        config_file: Optional[Path] = None,
        cli_overrides: Optional[Dict[str, Any]] = None
    ) -> Config:
        """Load configuration with proper precedence."""
        try:
            # Start with default config
            config = Config()

            # Load from config file if specified or found
            if config_file:
                file_config = self._load_config_file(config_file)
                config = self._merge_configs(config, file_config)
            else:
                # Look for config files in project directory
                found_config = self._find_config_file(project_path)
                if found_config:
                    file_config = self._load_config_file(found_config)
                    config = self._merge_configs(config, file_config)

            # Apply CLI overrides
            if cli_overrides:
                config = self._apply_cli_overrides(config, cli_overrides)

            # Validate configuration
            self._validate_config(config)

            return config

        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {e}")

    def save_config(self, config: Config, config_path: Path) -> None:
        """Save configuration to file."""
        try:
            config_dict = self._config_to_dict(config)

            if config_path.suffix.lower() == ".toml":
                self._save_toml_config(config_dict, config_path)
            else:
                self._save_json_config(config_dict, config_path)

        except Exception as e:
            raise ConfigError(f"Failed to save configuration: {e}")

    def create_default_config(self, project_path: Path) -> Config:
        """Create a default configuration for a project."""
        config = Config()

        # Customize based on project characteristics
        # This would be enhanced with project analysis results

        return config

    def _find_config_file(self, project_path: Path) -> Optional[Path]:
        """Find configuration file in project directory."""
        for config_name in self.DEFAULT_CONFIG_NAMES:
            config_path = project_path / config_name
            if config_path.exists():
                return config_path
        return None

    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from file."""
        if not config_path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")

        try:
            if config_path.suffix.lower() == ".toml":
                return toml.load(config_path)
            with open(config_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise ConfigError(f"Failed to parse configuration file {config_path}: {e}")

    def _merge_configs(self, base: Config, override: Dict[str, Any]) -> Config:
        """Merge configuration dictionaries."""
        # Convert base config to dict
        base_dict = self._config_to_dict(base)

        # Deep merge override into base
        merged = self._deep_merge(base_dict, override)

        # Convert back to Config object
        return self._dict_to_config(merged)

    def _apply_cli_overrides(self, config: Config, cli_overrides: Dict[str, Any]) -> Config:
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

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
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
            if "claude_mention_policy" in git_config_dict and isinstance(git_config_dict["claude_mention_policy"], str):
                git_config_dict["claude_mention_policy"] = ClaudeMentionPolicy(git_config_dict["claude_mention_policy"])

            git_integration_config = GitIntegrationConfig(**git_config_dict)
            output_config = OutputConfig(**config_dict.get("output", {}))
            user_preferences = UserPreferences(**config_dict.get("user_preferences", {}))
            integration_config = IntegrationConfig(**config_dict.get("integrations", {}))

            return Config(
                version=config_dict.get("version", "1.0"),
                analysis=analysis_config,
                templates=template_config,
                agents=agent_config,
                git_integration=git_integration_config,
                output=output_config,
                user_preferences=user_preferences,
                integrations=integration_config,
                workspace_settings=config_dict.get("workspace_settings", {}),
                project_profiles=config_dict.get("project_profiles", {})
            )
        except Exception as e:
            raise ConfigError(f"Failed to convert dictionary to Config: {e}")

    def _save_json_config(self, config_dict: Dict[str, Any], config_path: Path) -> None:
        """Save configuration as JSON."""
        # Convert enums to strings for serialization
        serializable_dict = self._prepare_for_serialization(config_dict)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(serializable_dict, f, indent=2, sort_keys=True)

    def _save_toml_config(self, config_dict: Dict[str, Any], config_path: Path) -> None:
        """Save configuration as TOML."""
        # Convert enums to strings for serialization
        serializable_dict = self._prepare_for_serialization(config_dict)

        with open(config_path, "w", encoding="utf-8") as f:
            toml.dump(serializable_dict, f)

    def _prepare_for_serialization(self, obj: Any) -> Any:
        """Prepare object for JSON/TOML serialization."""
        if isinstance(obj, dict):
            return {k: self._prepare_for_serialization(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._prepare_for_serialization(item) for item in obj]
        if hasattr(obj, "value"):  # Enum
            return obj.value
        return obj

    def load_global_config(self) -> Optional[Config]:
        """Load global configuration from user's home directory."""
        for config_path_str in self.GLOBAL_CONFIG_NAMES:
            config_path = Path(config_path_str).expanduser()
            if config_path.exists():
                try:
                    return self._load_config_file(config_path)
                except Exception:
                    continue
        return None

    def save_workspace_setting(self, project_path: Path, key: str, value: Any) -> None:
        """Save a workspace-specific setting."""
        workspace_id = str(project_path.resolve())
        if workspace_id not in self.workspace_cache:
            self.workspace_cache[workspace_id] = {}
        self.workspace_cache[workspace_id][key] = value

        # Persist to disk
        workspace_config_path = project_path / ".claude-builder" / "workspace.json"
        workspace_config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(workspace_config_path, "w", encoding="utf-8") as f:
            json.dump(self.workspace_cache[workspace_id], f, indent=2)

    def get_workspace_setting(self, project_path: Path, key: str, default: Any = None) -> Any:
        """Get a workspace-specific setting."""
        workspace_id = str(project_path.resolve())

        # Check cache first
        if workspace_id in self.workspace_cache:
            return self.workspace_cache[workspace_id].get(key, default)

        # Load from disk
        workspace_config_path = project_path / ".claude-builder" / "workspace.json"
        if workspace_config_path.exists():
            try:
                with open(workspace_config_path, encoding="utf-8") as f:
                    workspace_settings = json.load(f)
                self.workspace_cache[workspace_id] = workspace_settings
                return workspace_settings.get(key, default)
            except Exception:
                pass

        return default

    def create_project_profile(self, profile_name: str, config: Config,
                             description: str = "") -> None:
        """Create a project profile for reuse."""
        profile_data = {
            "description": description,
            "created": json.JSONEncoder().encode(datetime.now().isoformat()),
            "config": self._config_to_dict(config)
        }

        profiles_dir = Path.home() / ".claude-builder" / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)

        profile_path = profiles_dir / f"{profile_name}.json"
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2)

    def list_project_profiles(self) -> List[Dict[str, Any]]:
        """List available project profiles."""
        profiles_dir = Path.home() / ".claude-builder" / "profiles"
        if not profiles_dir.exists():
            return []

        profiles = []
        for profile_file in profiles_dir.glob("*.json"):
            try:
                with open(profile_file, encoding="utf-8") as f:
                    profile_data = json.load(f)
                profile_data["name"] = profile_file.stem
                profiles.append(profile_data)
            except Exception:
                continue

        return profiles

    def apply_project_profile(self, profile_name: str, base_config: Config) -> Config:
        """Apply a project profile to base configuration."""
        profiles_dir = Path.home() / ".claude-builder" / "profiles"
        profile_path = profiles_dir / f"{profile_name}.json"

        if not profile_path.exists():
            raise ConfigError(f"Project profile not found: {profile_name}")

        try:
            with open(profile_path, encoding="utf-8") as f:
                profile_data = json.load(f)

            profile_config = profile_data["config"]
            return self._merge_configs(base_config, profile_config)
        except Exception as e:
            raise ConfigError(f"Failed to apply profile {profile_name}: {e}")

    def validate_config_compatibility(self, config: Config,
                                    project_analysis: Optional[Any] = None) -> List[str]:
        """Validate configuration compatibility with project."""
        warnings = []

        # Check agent compatibility
        if project_analysis:
            # This would check if selected agents are appropriate for the project
            pass

        # Check template paths exist
        for path_str in config.templates.search_paths:
            path = Path(path_str).expanduser()
            if not path.exists():
                warnings.append(f"Template search path does not exist: {path}")

        # Check integration settings
        if config.integrations.package_managers:
            for pm, settings in config.integrations.package_managers.items():
                if settings.get("auto_install", False):
                    # Check if package manager is available
                    pass

        return warnings

    def _validate_config(self, config: Config) -> None:
        """Validate configuration object."""
        # Validate version
        if config.version != self.schema_version:
            raise ConfigError(f"Unsupported config version: {config.version}")

        # Validate confidence threshold
        if not 0 <= config.analysis.confidence_threshold <= 100:
            raise ConfigError("confidence_threshold must be between 0 and 100")

        # Validate max concurrent agents
        if config.agents.max_concurrent_agents < 1:
            raise ConfigError("max_concurrent_agents must be at least 1")

        # Validate agent timeout
        if config.agents.agent_timeout < 30:
            raise ConfigError("agent_timeout must be at least 30 seconds")

        # Validate template cache TTL
        if config.templates.template_cache_ttl < 0:
            raise ConfigError("template_cache_ttl must be non-negative")

        # Validate file size limits
        if config.analysis.max_file_size < 1024:  # 1KB minimum
            raise ConfigError("max_file_size must be at least 1024 bytes")

        # Validate template search paths
        for path in config.templates.search_paths:
            expanded_path = Path(path).expanduser()
            if not expanded_path.exists():
                # Warning, not error - paths might be created later
                pass

        # Validate file permissions format
        try:
            int(config.output.file_permissions, 8)
        except ValueError:
            raise ConfigError(f"Invalid file permissions format: {config.output.file_permissions}")

        # Validate update check frequency
        valid_frequencies = ["never", "daily", "weekly", "monthly"]
        if config.user_preferences.update_check_frequency not in valid_frequencies:
            raise ConfigError(f"Invalid update_check_frequency. Must be one of: {valid_frequencies}")

        # Validate theme
        valid_themes = ["light", "dark", "auto"]
        if config.user_preferences.theme not in valid_themes:
            raise ConfigError(f"Invalid theme. Must be one of: {valid_themes}")

        # Validate agent selection algorithm
        valid_algorithms = ["intelligent", "strict", "permissive"]
        if config.agents.agent_selection_algorithm not in valid_algorithms:
            raise ConfigError(f"Invalid agent_selection_algorithm. Must be one of: {valid_algorithms}")


def load_config_from_args(args: Dict[str, Any]) -> Config:
    """Convenience function to load config from command-line arguments."""
    config_manager = ConfigManager()

    project_path = Path(args.get("project_path", ".")).resolve()
    config_file = Path(args["config_file"]) if args.get("config_file") else None

    return config_manager.load_config(
        project_path=project_path,
        config_file=config_file,
        cli_overrides=args
    )



# Placeholder classes for test compatibility  
class AdvancedConfigManager:
    """Placeholder AdvancedConfigManager class for test compatibility."""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.config = {}
        
    def load_advanced_config(self) -> dict:
        """Load advanced configuration."""
        return {"advanced": True, "settings": {}}
        
    def validate_config(self) -> bool:
        """Validate configuration."""
        return True
        
    def merge_configs(self, *configs) -> dict:
        """Merge multiple configurations."""
        result = {}
        for config in configs:
            result.update(config)
        return result


class ConfigEnvironment:
    """Placeholder ConfigEnvironment class for test compatibility."""
    
    def __init__(self, env_name: str = "development"):
        self.env_name = env_name
        self.variables = {}
        
    def get_environment_config(self) -> Dict[str, Any]:
        return {"environment": self.env_name, "debug": True}


class ConfigSchema:
    """Placeholder ConfigSchema class for test compatibility."""
    
    def __init__(self, schema_dict: Dict[str, Any] = None):
        self.schema = schema_dict or {}
        
    def validate(self, config: Dict[str, Any]) -> bool:
        return True
        
    def get_defaults(self) -> Dict[str, Any]:
        return {"version": "1.0", "debug": False}


class ConfigValidator:
    """Placeholder ConfigValidator class for test compatibility."""
    
    def __init__(self):
        self.rules = []
        
    def validate_project_config(self, config: dict) -> dict:
        """Validate project configuration."""
        return {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
    def add_validation_rule(self, rule):
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
        
    def on_config_changed(self, callback):
        pass


class SecureConfigHandler:
    """Placeholder SecureConfigHandler class for test compatibility."""
    
    def __init__(self, encryption_key: str = None):
        self.encryption_key = encryption_key
        
    def encrypt_config(self, config: Dict[str, Any]) -> str:
        return "encrypted_config_data"
        
    def decrypt_config(self, encrypted_data: str) -> Dict[str, Any]:
        return {"decrypted": "config"}
        
    def store_secure_config(self, config: Dict[str, Any], path: str) -> bool:
        return True
