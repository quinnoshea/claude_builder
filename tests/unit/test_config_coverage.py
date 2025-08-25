"""Additional tests for core.config module to boost coverage."""

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
from claude_builder.core.models import ClaudeMentionPolicy, GitIntegrationMode
from claude_builder.utils.exceptions import ConfigError


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def test_config_creation_basic():
    """Test basic Config creation - covers Config.__init__."""
    config = Config()

    assert config.version == "1.0"
    assert isinstance(config.analysis, AnalysisConfig)
    assert isinstance(config.templates, TemplateConfig)
    assert isinstance(config.agents, AgentConfig)
    assert isinstance(config.git_integration, GitIntegrationConfig)
    assert isinstance(config.output, OutputConfig)
    assert isinstance(config.user_preferences, UserPreferences)


def test_analysis_config_creation():
    """Test AnalysisConfig creation and defaults - covers AnalysisConfig."""
    config = AnalysisConfig()

    assert config.cache_enabled is True
    assert config.parallel_processing is True
    assert config.confidence_threshold == 80
    assert ".git/" in config.ignore_patterns
    assert "node_modules/" in config.ignore_patterns
    assert "__pycache__/" in config.ignore_patterns
    assert config.overrides == {}


def test_template_config_creation():
    """Test TemplateConfig creation and defaults - covers TemplateConfig."""
    config = TemplateConfig()

    assert "./templates/" in config.search_paths
    assert "~/.claude-builder/templates/" in config.search_paths
    assert isinstance(config.preferred_templates, list)
    assert config.preferred_templates == []
    assert isinstance(config.template_overrides, dict)
    assert config.template_overrides == {}
    assert config.auto_update_templates is False


def test_agent_config_creation():
    """Test AgentConfig creation and defaults - covers AgentConfig."""
    config = AgentConfig()

    assert config.install_automatically is True
    assert isinstance(config.exclude_agents, list)
    assert config.exclude_agents == []
    assert isinstance(config.priority_agents, list)
    assert config.priority_agents == []
    assert isinstance(config.workflows, dict)
    assert "feature_development" in config.workflows
    assert "bug_fixing" in config.workflows
    assert config.agent_selection_algorithm == "intelligent"
    assert config.max_concurrent_agents == 5


def test_git_integration_config_creation():
    """Test GitIntegrationConfig creation and defaults - covers GitIntegrationConfig."""
    config = GitIntegrationConfig()

    assert config.enabled is True
    assert config.mode == GitIntegrationMode.NO_INTEGRATION
    assert config.claude_mention_policy == ClaudeMentionPolicy.MINIMAL
    assert config.backup_before_changes is True
    assert "CLAUDE.md" in config.files_to_exclude
    assert "AGENTS.md" in config.files_to_exclude
    assert ".claude/" in config.files_to_exclude


def test_output_config_creation():
    """Test OutputConfig creation and defaults - covers OutputConfig."""
    config = OutputConfig()

    assert config.format == "files"
    assert config.backup_existing is True
    assert config.create_directories is True
    assert config.file_permissions == "0644"
    assert config.validate_generated is True


def test_user_preferences_creation():
    """Test UserPreferences creation and defaults - covers UserPreferences."""
    config = UserPreferences()

    assert config.default_editor == "code"
    assert config.prefer_verbose_output is False
    assert config.auto_open_generated_files is False
    assert config.confirmation_prompts is True
    assert config.theme == "auto"
    assert config.language == "en"
    assert config.analytics_enabled is True
    assert config.update_check_frequency == "weekly"
    assert config.update_check_frequency == "weekly"


def test_config_manager_initialization():
    """Test ConfigManager initialization - covers ConfigManager.__init__."""
    manager = ConfigManager()

    assert manager.schema_version == "1.0"
    assert isinstance(manager.DEFAULT_CONFIG_NAMES, list)
    assert "claude-builder.json" in manager.DEFAULT_CONFIG_NAMES
    assert "claude-builder.toml" in manager.DEFAULT_CONFIG_NAMES
    assert ".claude-builder.json" in manager.DEFAULT_CONFIG_NAMES
    assert ".claude-builder.toml" in manager.DEFAULT_CONFIG_NAMES


def test_config_manager_find_config_file_json(temp_dir):
    """Test finding JSON config file - covers find_config_file method."""
    config_file = temp_dir / "claude-builder.json"
    config_file.write_text('{"version": "1.0"}')

    manager = ConfigManager()
    found_file = manager._find_config_file(temp_dir)

    assert found_file == config_file


def test_config_manager_find_config_file_toml(temp_dir):
    """Test finding TOML config file - covers find_config_file method."""
    config_file = temp_dir / "claude-builder.toml"
    config_file.write_text('version = "1.0"')

    manager = ConfigManager()
    found_file = manager._find_config_file(temp_dir)

    assert found_file == config_file


def test_config_manager_find_config_file_none(temp_dir):
    """Test finding no config file - covers find_config_file method."""
    manager = ConfigManager()
    found_file = manager._find_config_file(temp_dir)

    assert found_file is None


def test_config_manager_load_default_config(temp_dir):
    """Test loading default configuration - covers load_config default path."""
    manager = ConfigManager()

    config = manager.load_config(temp_dir)

    assert isinstance(config, Config)
    assert config.version == "1.0"
    assert isinstance(config.analysis, AnalysisConfig)
    assert isinstance(config.templates, TemplateConfig)


def test_config_manager_load_json_config(temp_dir):
    """Test loading JSON configuration - covers load_config with JSON."""
    config_data = {
        "version": "1.0",
        "analysis": {
            "confidence_threshold": 85,
            "cache_enabled": False,
            "parallel_processing": False,
        },
        "user_preferences": {"prefer_verbose_output": True, "default_editor": "vim"},
    }

    config_file = temp_dir / "claude-builder.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f)

    manager = ConfigManager()
    config = manager.load_config(temp_dir)

    assert config.analysis.confidence_threshold == 85
    assert config.analysis.cache_enabled is False
    assert config.analysis.parallel_processing is False
    assert config.user_preferences.prefer_verbose_output is True
    assert config.user_preferences.default_editor == "vim"


def test_config_manager_load_toml_config(temp_dir):
    """Test loading TOML configuration - covers load_config with TOML."""
    config_data = {
        "version": "1.0",
        "templates": {
            "preferred_templates": ["python-web", "rust-cli"],
            "auto_update_templates": True,
        },
        "git_integration": {"enabled": False, "claude_mention_policy": "forbidden"},
    }

    config_file = temp_dir / "claude-builder.toml"
    with open(config_file, "w") as f:
        toml.dump(config_data, f)

    manager = ConfigManager()
    config = manager.load_config(temp_dir)

    assert "python-web" in config.templates.preferred_templates
    assert "rust-cli" in config.templates.preferred_templates
    assert config.templates.auto_update_templates is True
    assert config.git_integration.enabled is False
    assert config.git_integration.claude_mention_policy == ClaudeMentionPolicy.FORBIDDEN


def test_config_manager_save_json_config(temp_dir):
    """Test saving JSON configuration - covers save_config with JSON."""
    config = Config()
    config.analysis.confidence_threshold = 90
    config.user_preferences.prefer_verbose_output = True

    config_file = temp_dir / "test-config.json"
    manager = ConfigManager()
    manager.save_config(config, config_file)

    assert config_file.exists()

    # Verify saved content
    with open(config_file) as f:
        saved_data = json.load(f)

    assert saved_data["analysis"]["confidence_threshold"] == 90
    assert saved_data["user_preferences"]["prefer_verbose_output"] is True


def test_config_manager_save_toml_config(temp_dir):
    """Test saving TOML configuration - covers save_config with TOML."""
    config = Config()
    config.templates.preferred_templates = ["custom-template"]
    config.agents.exclude_agents = ["deprecated-agent"]

    config_file = temp_dir / "test-config.toml"
    manager = ConfigManager()
    manager.save_config(config, config_file)

    assert config_file.exists()

    # Verify saved content
    with open(config_file) as f:
        saved_data = toml.load(f)

    assert "custom-template" in saved_data["templates"]["preferred_templates"]
    assert "deprecated-agent" in saved_data["agents"]["exclude_agents"]


def test_config_manager_cli_overrides(temp_dir):
    """Test CLI argument overrides - covers apply_cli_overrides."""
    cli_args = {
        "verbose": True,
        "template": "override-template",
        "claude_mentions": "forbidden",
        "no_git": True,
        "backup_existing": False,
        "output_format": "json",
    }

    manager = ConfigManager()
    config = manager.load_config(temp_dir, cli_overrides=cli_args)

    assert config.user_preferences.prefer_verbose_output is True
    assert "override-template" in config.templates.preferred_templates
    assert config.git_integration.claude_mention_policy == ClaudeMentionPolicy.FORBIDDEN
    assert config.git_integration.enabled is False
    assert config.output.backup_existing is False
    assert config.output.format == "json"


def test_config_manager_validation_success():
    """Test successful configuration validation - covers _validate_config success path."""
    config = Config()
    manager = ConfigManager()

    # Should not raise any exceptions
    manager._validate_config(config)


def test_config_manager_validation_invalid_confidence():
    """Test validation fails for invalid confidence - covers _validate_config error path."""
    config = Config()
    config.analysis.confidence_threshold = 150  # Invalid: > 100

    manager = ConfigManager()

    with pytest.raises(
        ConfigError, match="confidence_threshold must be between 0 and 100"
    ):
        manager._validate_config(config)


def test_config_manager_validation_invalid_permissions():
    """Test validation fails for invalid permissions - covers _validate_config error path."""
    config = Config()
    config.output.file_permissions = "invalid"

    manager = ConfigManager()

    with pytest.raises(ConfigError, match="Invalid file permissions format"):
        manager._validate_config(config)


def test_config_manager_validation_unsupported_version():
    """Test validation fails for unsupported version - covers _validate_config error path."""
    config = Config()
    config.version = "2.0"  # Unsupported version

    manager = ConfigManager()

    with pytest.raises(ConfigError, match="Unsupported config version"):
        manager._validate_config(config)


def test_config_manager_deep_merge():
    """Test deep merging of configurations - covers _deep_merge method."""
    manager = ConfigManager()

    base = {
        "analysis": {
            "confidence_threshold": 80,
            "cache_enabled": True,
            "parallel_processing": True,
        },
        "templates": {"search_paths": ["./templates/"]},
    }

    override = {
        "analysis": {
            "confidence_threshold": 90
            # Other values should be preserved
        },
        "git_integration": {"enabled": False},
    }

    result = manager._deep_merge(base, override)

    assert result["analysis"]["confidence_threshold"] == 90
    assert result["analysis"]["cache_enabled"] is True  # Preserved
    assert result["analysis"]["parallel_processing"] is True  # Preserved
    assert result["git_integration"]["enabled"] is False
    assert result["templates"]["search_paths"] == ["./templates/"]


def test_config_manager_enum_serialization(temp_dir):
    """Test enum serialization - covers enum handling in save_config."""
    config = Config()
    config.git_integration.mode = GitIntegrationMode.EXCLUDE_GENERATED
    config.git_integration.claude_mention_policy = ClaudeMentionPolicy.FORBIDDEN

    config_file = temp_dir / "enum-test.json"
    manager = ConfigManager()
    manager.save_config(config, config_file)

    # Check raw JSON for enum values
    with open(config_file) as f:
        saved_data = json.load(f)

    assert saved_data["git_integration"]["mode"] == "exclude_generated"
    assert saved_data["git_integration"]["claude_mention_policy"] == "forbidden"


def test_config_manager_enum_deserialization(temp_dir):
    """Test enum deserialization - covers enum handling in load_config."""
    config_data = {
        "version": "1.0",
        "git_integration": {"claude_mention_policy": "minimal"},
    }

    config_file = temp_dir / "enum-test.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f)

    manager = ConfigManager()
    config = manager.load_config(temp_dir)

    # Note: enum deserialization currently only works for claude_mention_policy
    assert config.git_integration.claude_mention_policy == ClaudeMentionPolicy.MINIMAL
    # mode remains at default due to enum deserialization issue
    assert config.git_integration.mode == GitIntegrationMode.NO_INTEGRATION


def test_config_manager_create_default_config(temp_dir):
    """Test creating default config for project - covers create_default_config."""
    manager = ConfigManager()
    config = manager.create_default_config(temp_dir)

    assert isinstance(config, Config)
    assert config.version == "1.0"
    # Should have all required components
    assert isinstance(config.analysis, AnalysisConfig)
    assert isinstance(config.templates, TemplateConfig)
    assert isinstance(config.agents, AgentConfig)


def test_load_config_from_args_helper():
    """Test the load_config_from_args helper function - covers helper function."""
    args = {
        "project_path": "/test/path",
        "verbose": True,
        "template": "test-template",
        "output_format": "json",
    }

    config = load_config_from_args(args)

    assert isinstance(config, Config)
    assert config.user_preferences.prefer_verbose_output is True
    assert "test-template" in config.templates.preferred_templates
    assert config.output.format == "json"


# Error handling tests
def test_config_manager_invalid_json_file(temp_dir):
    """Test handling of invalid JSON config file - covers error handling."""
    config_file = temp_dir / "claude-builder.json"
    config_file.write_text("{ invalid json content")

    manager = ConfigManager()

    with pytest.raises(ConfigError, match="Failed to parse configuration file"):
        manager.load_config(temp_dir)


def test_config_manager_invalid_toml_file(temp_dir):
    """Test handling of invalid TOML config file - covers error handling."""
    config_file = temp_dir / "claude-builder.toml"
    config_file.write_text("[ invalid toml")

    manager = ConfigManager()

    with pytest.raises(ConfigError, match="Failed to parse configuration file"):
        manager.load_config(temp_dir)


def test_config_manager_nonexistent_explicit_file(temp_dir):
    """Test handling of explicit nonexistent config file - covers error handling."""
    nonexistent_file = temp_dir / "nonexistent.json"

    manager = ConfigManager()

    with pytest.raises(ConfigError, match="Configuration file not found"):
        manager.load_config(temp_dir, config_file=nonexistent_file)
