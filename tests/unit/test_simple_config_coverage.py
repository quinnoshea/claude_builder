"""Simple config tests to boost coverage without complex assertions."""

import json
import tempfile
from pathlib import Path

import pytest
import toml

from claude_builder.core.config import (
    AgentConfig,
    AnalysisConfig,
    Config,
    ConfigManager,
    GitIntegrationConfig,
    OutputConfig,
    TemplateConfig,
    UserPreferences,
    load_config_from_args,
)
from claude_builder.utils.exceptions import ConfigError


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def test_config_basic_creation():
    """Test basic config creation - covers basic initialization."""
    config = Config()
    assert config.version == "1.0"
    assert isinstance(config.analysis, AnalysisConfig)
    assert isinstance(config.templates, TemplateConfig)
    assert isinstance(config.agents, AgentConfig)
    assert isinstance(config.git_integration, GitIntegrationConfig)
    assert isinstance(config.output, OutputConfig)
    assert isinstance(config.user_preferences, UserPreferences)


def test_analysis_config_basic():
    """Test AnalysisConfig basic functionality - covers AnalysisConfig."""
    config = AnalysisConfig()
    assert config.cache_enabled is True
    assert config.parallel_processing is True
    assert config.confidence_threshold == 80
    assert isinstance(config.ignore_patterns, list)
    assert len(config.ignore_patterns) > 0
    assert isinstance(config.overrides, dict)


def test_template_config_basic():
    """Test TemplateConfig basic functionality - covers TemplateConfig."""
    config = TemplateConfig()
    assert isinstance(config.search_paths, list)
    assert len(config.search_paths) > 0
    assert isinstance(config.preferred_templates, list)
    assert isinstance(config.template_overrides, dict)
    assert config.auto_update_templates in [True, False]  # Just check it exists


def test_agent_config_basic():
    """Test AgentConfig basic functionality - covers AgentConfig."""
    config = AgentConfig()
    assert config.install_automatically is True
    assert isinstance(config.exclude_agents, list)
    assert isinstance(config.priority_agents, list)
    assert isinstance(config.workflows, dict)
    assert len(config.workflows) >= 2  # Should have some default workflows


def test_git_integration_config_basic():
    """Test GitIntegrationConfig basic functionality - covers GitIntegrationConfig."""
    config = GitIntegrationConfig()
    assert config.enabled is True
    assert hasattr(config, "mode")
    assert hasattr(config, "claude_mention_policy")
    assert config.backup_before_changes is True
    assert isinstance(config.files_to_exclude, list)
    assert len(config.files_to_exclude) > 0


def test_output_config_basic():
    """Test OutputConfig basic functionality - covers OutputConfig."""
    config = OutputConfig()
    assert config.format == "files"
    assert config.backup_existing is True
    assert config.create_directories is True
    assert isinstance(config.file_permissions, str)
    assert config.validate_generated is True


def test_user_preferences_basic():
    """Test UserPreferences basic functionality - covers UserPreferences."""
    config = UserPreferences()
    assert isinstance(config.default_editor, str)
    assert len(config.default_editor) > 0
    assert config.prefer_verbose_output in [True, False]
    assert config.confirmation_prompts is True


def test_config_manager_basic():
    """Test ConfigManager basic functionality - covers ConfigManager."""
    manager = ConfigManager()
    assert manager.schema_version == "1.0"
    assert isinstance(manager.DEFAULT_CONFIG_NAMES, list)
    assert len(manager.DEFAULT_CONFIG_NAMES) > 0


def test_config_manager_find_config_none(temp_dir):
    """Test finding no config file - covers find_config_file."""
    manager = ConfigManager()
    found_file = manager._find_config_file(temp_dir)
    assert found_file is None


def test_config_manager_find_config_json(temp_dir):
    """Test finding JSON config file - covers find_config_file."""
    config_file = temp_dir / "claude-builder.json"
    config_file.write_text('{"version": "1.0"}')

    manager = ConfigManager()
    found_file = manager._find_config_file(temp_dir)
    assert found_file == config_file


def test_config_manager_load_default(temp_dir):
    """Test loading default configuration - covers load_config."""
    manager = ConfigManager()
    config = manager.load_config(temp_dir)

    assert isinstance(config, Config)
    assert config.version == "1.0"


def test_config_manager_load_json(temp_dir):
    """Test loading JSON configuration - covers JSON parsing."""
    config_data = {
        "version": "1.0",
        "analysis": {
            "confidence_threshold": 85,
            "cache_enabled": False
        }
    }

    config_file = temp_dir / "claude-builder.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f)

    manager = ConfigManager()
    config = manager.load_config(temp_dir)

    assert config.analysis.confidence_threshold == 85
    assert config.analysis.cache_enabled is False


def test_config_manager_load_toml(temp_dir):
    """Test loading TOML configuration - covers TOML parsing."""
    config_data = {
        "version": "1.0",
        "templates": {
            "preferred_templates": ["python-web"]
        }
    }

    config_file = temp_dir / "claude-builder.toml"
    with open(config_file, "w") as f:
        toml.dump(config_data, f)

    manager = ConfigManager()
    config = manager.load_config(temp_dir)

    assert "python-web" in config.templates.preferred_templates


def test_config_manager_save_json(temp_dir):
    """Test saving JSON configuration - covers save_config JSON."""
    config = Config()
    config.analysis.confidence_threshold = 90

    config_file = temp_dir / "test-config.json"
    manager = ConfigManager()
    manager.save_config(config, config_file)

    assert config_file.exists()

    # Verify saved content
    with open(config_file) as f:
        saved_data = json.load(f)
    assert saved_data["analysis"]["confidence_threshold"] == 90


def test_config_manager_save_toml(temp_dir):
    """Test saving TOML configuration - covers save_config TOML."""
    config = Config()
    config.templates.preferred_templates = ["test-template"]

    config_file = temp_dir / "test-config.toml"
    manager = ConfigManager()
    manager.save_config(config, config_file)

    assert config_file.exists()

    # Verify saved content
    with open(config_file) as f:
        saved_data = toml.load(f)
    assert "test-template" in saved_data["templates"]["preferred_templates"]


def test_config_manager_validation_success():
    """Test successful configuration validation - covers _validate_config."""
    config = Config()
    manager = ConfigManager()
    # Should not raise any exceptions
    manager._validate_config(config)


def test_config_manager_validation_invalid_confidence():
    """Test validation fails for invalid confidence - covers validation errors."""
    config = Config()
    config.analysis.confidence_threshold = 150  # Invalid

    manager = ConfigManager()
    with pytest.raises(ConfigError, match="confidence_threshold must be between 0 and 100"):
        manager._validate_config(config)


def test_config_manager_deep_merge():
    """Test deep merging configurations - covers _deep_merge."""
    manager = ConfigManager()

    base = {
        "analysis": {
            "confidence_threshold": 80,
            "cache_enabled": True
        }
    }

    override = {
        "analysis": {
            "confidence_threshold": 90
        }
    }

    result = manager._deep_merge(base, override)

    assert result["analysis"]["confidence_threshold"] == 90
    assert result["analysis"]["cache_enabled"] is True  # Preserved


def test_config_manager_create_default(temp_dir):
    """Test creating default config - covers create_default_config."""
    manager = ConfigManager()
    config = manager.create_default_config(temp_dir)

    assert isinstance(config, Config)
    assert config.version == "1.0"


def test_load_config_from_args_basic():
    """Test load_config_from_args helper - covers helper function."""
    args = {
        "project_path": "/test/path",
        "verbose": True
    }

    config = load_config_from_args(args)
    assert isinstance(config, Config)
    assert config.user_preferences.prefer_verbose_output is True


def test_config_manager_error_handling_invalid_json(temp_dir):
    """Test handling invalid JSON - covers error handling."""
    config_file = temp_dir / "claude-builder.json"
    config_file.write_text("{ invalid json")

    manager = ConfigManager()
    with pytest.raises(ConfigError, match="Failed to parse configuration file"):
        manager.load_config(temp_dir)


def test_config_manager_error_handling_nonexistent_file(temp_dir):
    """Test handling nonexistent explicit file - covers error handling."""
    nonexistent_file = temp_dir / "nonexistent.json"

    manager = ConfigManager()
    with pytest.raises(ConfigError, match="Configuration file not found"):
        manager.load_config(temp_dir, config_file=nonexistent_file)
