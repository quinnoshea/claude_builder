"""Configuration environment for workspace and profile management."""

import json

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

from claude_builder.utils.exceptions import ConfigError


if TYPE_CHECKING:
    from claude_builder.core.config import Config


# Constants imported from parent module
PROJECT_PROFILE_NOT_FOUND = "Project profile not found"
FAILED_TO_APPLY_PROFILE = "Failed to apply profile"


class ConfigEnvironment:
    """Handles environment-specific configuration and workspace management."""

    def __init__(self) -> None:
        self.workspace_cache: Dict[str, Any] = {}
        self.profiles_path = Path("~/.config/claude-builder/profiles").expanduser()

    def save_workspace_setting(self, project_path: Path, key: str, value: Any) -> None:
        """Save a workspace-specific setting."""
        project_key = str(project_path.resolve())

        if project_key not in self.workspace_cache:
            self.workspace_cache[project_key] = {}

        self.workspace_cache[project_key][key] = value

        # Persist to disk
        self._save_workspace_cache()

    def get_workspace_setting(
        self, project_path: Path, key: str, default: Any = None
    ) -> Any:
        """Get a workspace-specific setting."""
        project_key = str(project_path.resolve())

        if project_key not in self.workspace_cache:
            self._load_workspace_cache()

        return self.workspace_cache.get(project_key, {}).get(key, default)

    def _save_workspace_cache(self) -> None:
        """Save workspace cache to disk."""
        cache_path = Path("~/.config/claude-builder/workspace_cache.json").expanduser()
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(self.workspace_cache, f, indent=2)
        except Exception:
            # Fail silently for workspace cache
            pass

    def _load_workspace_cache(self) -> None:
        """Load workspace cache from disk."""
        cache_path = Path("~/.config/claude-builder/workspace_cache.json").expanduser()

        if cache_path.exists():
            try:
                with open(cache_path, encoding="utf-8") as f:
                    self.workspace_cache = json.load(f)
            except Exception:
                # Initialize empty cache on error
                self.workspace_cache = {}

    def create_project_profile(
        self, profile_name: str, config: Any, description: str = ""
    ) -> None:
        """Create a project profile for reuse."""
        self.profiles_path.mkdir(parents=True, exist_ok=True)

        profile_data = {
            "name": profile_name,
            "description": description,
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "config": asdict(config),
        }

        profile_file = self.profiles_path / f"{profile_name}.json"

        try:
            with open(profile_file, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, indent=2, default=str)
        except Exception as e:
            msg = f"Failed to create project profile '{profile_name}': {e}"
            raise ConfigError(msg)

    def list_project_profiles(self) -> List[Dict[str, Any]]:
        """List available project profiles."""
        if not self.profiles_path.exists():
            return []

        profiles = []

        for profile_file in self.profiles_path.glob("*.json"):
            try:
                with open(profile_file, encoding="utf-8") as f:
                    profile_data = json.load(f)
                    profiles.append(
                        {
                            "name": profile_data["name"],
                            "description": profile_data.get("description", ""),
                            "created_at": profile_data.get("created_at", ""),
                        }
                    )
            except Exception:
                # Skip invalid profile files
                continue

        return profiles

    def apply_project_profile(self, profile_name: str, base_config: Any) -> "Config":
        """Apply a project profile to base configuration."""
        profile_file = self.profiles_path / f"{profile_name}.json"

        if not profile_file.exists():
            msg = f"{PROJECT_PROFILE_NOT_FOUND}: {profile_name}"
            raise ConfigError(msg)

        try:
            with open(profile_file, encoding="utf-8") as f:
                profile_data = json.load(f)

            profile_config = profile_data["config"]

            # Import the necessary classes here to avoid circular imports

            # Merge profile config into base config
            base_dict = asdict(base_config)
            merged = self._deep_merge(base_dict, profile_config)

            # Convert back to Config object
            return self._dict_to_config(merged)

        except Exception as e:
            msg = f"{FAILED_TO_APPLY_PROFILE} '{profile_name}': {e}"
            raise ConfigError(msg)

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

    def _dict_to_config(self, config_dict: Dict[str, Any]) -> "Config":
        """Convert dictionary to Config object."""
        # Import here to avoid circular imports
        from claude_builder.core.config import (
            AgentConfig,
            AnalysisConfig,
            Config,
            GitIntegrationConfig,
            HealthConfig,
            IntegrationConfig,
            OutputConfig,
            TemplateConfig,
            UserPreferences,
        )
        from claude_builder.core.models import ClaudeMentionPolicy, GitIntegrationMode

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
            msg = f"Failed to convert dictionary to Config: {e}"
            raise ConfigError(msg) from e
