"""Configuration loader for file I/O operations."""

import json

from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional

import toml

from claude_builder.utils.exceptions import ConfigError


# Constants imported from parent module
FAILED_TO_LOAD_CONFIGURATION = "Failed to load configuration"
FAILED_TO_SAVE_CONFIGURATION = "Failed to save configuration"
CONFIGURATION_FILE_NOT_FOUND = "Configuration file not found"
FAILED_TO_PARSE_CONFIGURATION_FILE = "Failed to parse configuration file"


class ConfigLoader:
    """Handles configuration file loading and saving operations."""

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

    def find_config_file(self, project_path: Path) -> Optional[Path]:
        """Find configuration file in project directory."""
        for config_name in self.DEFAULT_CONFIG_NAMES:
            config_path = project_path / config_name
            if config_path.exists():
                return config_path
        return None

    def load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from file."""
        if not config_path.exists():
            msg = f"{CONFIGURATION_FILE_NOT_FOUND}: {config_path}"
            raise ConfigError(msg)

        try:
            if config_path.suffix.lower() == ".toml":
                return self._load_toml_config(config_path)
            return self._load_json_config(config_path)
        except Exception as e:
            msg = f"{FAILED_TO_PARSE_CONFIGURATION_FILE}: {config_path}: {e}"
            raise ConfigError(msg)

    def _load_json_config(self, config_path: Path) -> Dict[str, Any]:
        """Load JSON configuration file."""
        with open(config_path, encoding="utf-8") as f:
            result = json.load(f)
            return result if isinstance(result, dict) else {}

    def _load_toml_config(self, config_path: Path) -> Dict[str, Any]:
        """Load TOML configuration file."""
        with open(config_path, encoding="utf-8") as f:
            return toml.load(f)

    def save_json_config(self, config_dict: Dict[str, Any], config_path: Path) -> None:
        """Save configuration as JSON."""
        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            msg = f"{FAILED_TO_SAVE_CONFIGURATION} (JSON): {e}"
            raise ConfigError(msg) from e

    def save_toml_config(self, config_dict: Dict[str, Any], config_path: Path) -> None:
        """Save configuration as TOML."""
        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                toml.dump(config_dict, f)
        except Exception as e:
            msg = f"{FAILED_TO_SAVE_CONFIGURATION} (TOML): {e}"
            raise ConfigError(msg) from e

    def prepare_for_serialization(self, obj: Any) -> Any:
        """Prepare object for JSON/TOML serialization."""
        if isinstance(obj, dict):
            return {k: self.prepare_for_serialization(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.prepare_for_serialization(item) for item in obj]
        if hasattr(obj, "value"):  # Enum
            return obj.value
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        return obj

    def load_global_config(self) -> Optional[Dict[str, Any]]:
        """Load global configuration from user's home directory."""
        for config_name in self.GLOBAL_CONFIG_NAMES:
            config_path = Path(config_name).expanduser()
            if config_path.exists():
                try:
                    return self.load_config_file(config_path)
                except ConfigError:
                    # Continue to next config file
                    continue
        return None
