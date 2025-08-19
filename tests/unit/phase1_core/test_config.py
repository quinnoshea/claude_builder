"""Tests for Phase 1 core functionality: Configuration Management.

Tests cover the basic configuration system including:
- Configuration loading and saving
- Default configuration values
- Configuration validation
- CLI argument integration
"""

import pytest
import json
import toml
from pathlib import Path
from unittest.mock import Mock, patch

from claude_builder.core.config import (
    Config, ConfigManager, AnalysisConfig, TemplateConfig, 
    AgentConfig, GitIntegrationConfig, OutputConfig, UserPreferences
)
from claude_builder.core.models import GitIntegrationMode, ClaudeMentionPolicy
from claude_builder.utils.exceptions import ConfigError


@pytest.mark.unit
@pytest.mark.phase1
class TestConfig:
    """Test the main Config dataclass."""

    def test_default_config_creation(self):
        """Test creation of default configuration."""
        config = Config()
        
        assert config.version == '1.0'
        assert isinstance(config.analysis, AnalysisConfig)
        assert isinstance(config.templates, TemplateConfig)
        assert isinstance(config.agents, AgentConfig)
        assert isinstance(config.git_integration, GitIntegrationConfig)
        assert isinstance(config.output, OutputConfig)
        assert isinstance(config.user_preferences, UserPreferences)

    def test_analysis_config_defaults(self):
        """Test AnalysisConfig default values."""
        config = AnalysisConfig()
        
        assert config.cache_enabled is True
        assert config.parallel_processing is True
        assert config.confidence_threshold == 80
        assert '.git/' in config.ignore_patterns
        assert 'node_modules/' in config.ignore_patterns

    def test_template_config_defaults(self):
        """Test TemplateConfig default values."""
        config = TemplateConfig()
        
        assert './templates/' in config.search_paths
        assert '~/.claude-builder/templates/' in config.search_paths
        assert isinstance(config.preferred_templates, list)
        assert isinstance(config.template_overrides, dict)

    def test_agent_config_defaults(self):
        """Test AgentConfig default values."""
        config = AgentConfig()
        
        assert config.install_automatically is True
        assert isinstance(config.exclude_agents, list)
        assert isinstance(config.priority_agents, list)
        assert 'feature_development' in config.workflows
        assert 'bug_fixing' in config.workflows

    def test_git_integration_config_defaults(self):
        """Test GitIntegrationConfig default values."""
        config = GitIntegrationConfig()
        
        assert config.enabled is True
        assert config.mode == GitIntegrationMode.NO_INTEGRATION
        assert config.claude_mention_policy == ClaudeMentionPolicy.MINIMAL
        assert config.backup_before_changes is True
        assert 'CLAUDE.md' in config.files_to_exclude

    def test_output_config_defaults(self):
        """Test OutputConfig default values."""
        config = OutputConfig()
        
        assert config.format == 'files'
        assert config.backup_existing is True
        assert config.create_directories is True
        assert config.file_permissions == '0644'

    def test_user_preferences_defaults(self):
        """Test UserPreferences default values."""
        config = UserPreferences()
        
        assert config.default_editor == 'code'
        assert config.prefer_verbose_output is False
        assert config.confirmation_prompts is True


@pytest.mark.unit
@pytest.mark.phase1
class TestConfigManager:
    """Test the ConfigManager class."""

    def test_config_manager_initialization(self):
        """Test ConfigManager initializes correctly."""
        manager = ConfigManager()
        
        assert manager.schema_version == '1.0'
        assert isinstance(manager.DEFAULT_CONFIG_NAMES, list)
        assert 'claude-builder.json' in manager.DEFAULT_CONFIG_NAMES

    def test_load_default_config(self, temp_dir):
        """Test loading default configuration when no config file exists."""
        manager = ConfigManager()
        
        config = manager.load_config(temp_dir)
        
        assert isinstance(config, Config)
        assert config.version == '1.0'

    def test_load_json_config_file(self, temp_dir):
        """Test loading configuration from JSON file."""
        config_data = {
            'version': '1.0',
            'analysis': {
                'confidence_threshold': 70,
                'cache_enabled': False
            },
            'user_preferences': {
                'prefer_verbose_output': True
            }
        }
        
        config_file = temp_dir / 'claude-builder.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        manager = ConfigManager()
        config = manager.load_config(temp_dir)
        
        assert config.analysis.confidence_threshold == 70
        assert config.analysis.cache_enabled is False
        assert config.user_preferences.prefer_verbose_output is True

    def test_load_toml_config_file(self, temp_dir):
        """Test loading configuration from TOML file."""
        config_data = {
            'version': '1.0',
            'analysis': {
                'confidence_threshold': 90,
                'parallel_processing': False
            },
            'templates': {
                'preferred_templates': ['python-web', 'fastapi']
            }
        }
        
        config_file = temp_dir / 'claude-builder.toml'
        with open(config_file, 'w') as f:
            toml.dump(config_data, f)
        
        manager = ConfigManager()
        config = manager.load_config(temp_dir)
        
        assert config.analysis.confidence_threshold == 90
        assert config.analysis.parallel_processing is False
        assert 'python-web' in config.templates.preferred_templates

    def test_save_json_config(self, temp_dir):
        """Test saving configuration to JSON file."""
        config = Config()
        config.analysis.confidence_threshold = 85
        config.user_preferences.prefer_verbose_output = True
        
        config_file = temp_dir / 'test-config.json'
        manager = ConfigManager()
        manager.save_config(config, config_file)
        
        assert config_file.exists()
        
        # Load and verify
        with open(config_file) as f:
            saved_data = json.load(f)
        
        assert saved_data['analysis']['confidence_threshold'] == 85
        assert saved_data['user_preferences']['prefer_verbose_output'] is True

    def test_save_toml_config(self, temp_dir):
        """Test saving configuration to TOML file."""
        config = Config()
        config.templates.preferred_templates = ['rust-cli']
        
        config_file = temp_dir / 'test-config.toml'
        manager = ConfigManager()
        manager.save_config(config, config_file)
        
        assert config_file.exists()
        
        # Load and verify
        with open(config_file) as f:
            saved_data = toml.load(f)
        
        assert 'rust-cli' in saved_data['templates']['preferred_templates']

    def test_cli_overrides(self, temp_dir):
        """Test CLI argument overrides."""
        cli_args = {
            'verbose': True,
            'template': 'custom-template',
            'claude_mentions': 'forbidden',
            'no_git': True
        }
        
        manager = ConfigManager()
        config = manager.load_config(temp_dir, cli_overrides=cli_args)
        
        assert config.user_preferences.prefer_verbose_output is True
        assert 'custom-template' in config.templates.preferred_templates
        assert config.git_integration.claude_mention_policy == ClaudeMentionPolicy.FORBIDDEN
        assert config.git_integration.enabled is False

    def test_config_file_precedence(self, temp_dir):
        """Test configuration file precedence (JSON over TOML)."""
        # Create both JSON and TOML files
        json_config = temp_dir / 'claude-builder.json'
        toml_config = temp_dir / 'claude-builder.toml'
        
        json_data = {'analysis': {'confidence_threshold': 75}}
        toml_data = {'analysis': {'confidence_threshold': 85}}
        
        with open(json_config, 'w') as f:
            json.dump(json_data, f)
        
        with open(toml_config, 'w') as f:
            toml.dump(toml_data, f)
        
        manager = ConfigManager()
        config = manager.load_config(temp_dir)
        
        # JSON should take precedence
        assert config.analysis.confidence_threshold == 75

    def test_create_default_config_for_project(self, temp_dir):
        """Test creating default configuration for a project."""
        manager = ConfigManager()
        config = manager.create_default_config(temp_dir)
        
        assert isinstance(config, Config)
        assert config.version == '1.0'
        # Should create appropriate defaults based on project characteristics

    def test_config_validation_success(self):
        """Test successful configuration validation."""
        config = Config()
        manager = ConfigManager()
        
        # Should not raise any exceptions
        manager._validate_config(config)

    def test_config_validation_invalid_confidence_threshold(self):
        """Test validation fails for invalid confidence threshold."""
        config = Config()
        config.analysis.confidence_threshold = 150  # Invalid: > 100
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigError, match="confidence_threshold must be between 0 and 100"):
            manager._validate_config(config)

    def test_config_validation_invalid_file_permissions(self):
        """Test validation fails for invalid file permissions."""
        config = Config()
        config.output.file_permissions = 'invalid'
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigError, match="Invalid file permissions format"):
            manager._validate_config(config)

    def test_config_validation_unsupported_version(self):
        """Test validation fails for unsupported config version."""
        config = Config()
        config.version = '2.0'  # Unsupported version
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigError, match="Unsupported config version"):
            manager._validate_config(config)

    def test_deep_merge_configs(self):
        """Test deep merging of configuration dictionaries."""
        manager = ConfigManager()
        
        base = {
            'analysis': {
                'confidence_threshold': 80,
                'cache_enabled': True
            },
            'templates': {
                'search_paths': ['./templates/']
            }
        }
        
        override = {
            'analysis': {
                'confidence_threshold': 90
                # cache_enabled not specified, should remain True
            },
            'git_integration': {
                'enabled': False
            }
        }
        
        result = manager._deep_merge(base, override)
        
        assert result['analysis']['confidence_threshold'] == 90
        assert result['analysis']['cache_enabled'] is True
        assert result['git_integration']['enabled'] is False
        assert result['templates']['search_paths'] == ['./templates/']

    def test_enum_serialization(self, temp_dir):
        """Test proper serialization of enum values."""
        config = Config()
        config.git_integration.mode = GitIntegrationMode.EXCLUDE_GENERATED
        config.git_integration.claude_mention_policy = ClaudeMentionPolicy.FORBIDDEN
        
        config_file = temp_dir / 'enum-test.json'
        manager = ConfigManager()
        manager.save_config(config, config_file)
        
        # Load raw JSON to check enum serialization
        with open(config_file) as f:
            saved_data = json.load(f)
        
        assert saved_data['git_integration']['mode'] == 'exclude_generated'
        assert saved_data['git_integration']['claude_mention_policy'] == 'forbidden'

    def test_enum_deserialization(self, temp_dir):
        """Test proper deserialization of enum values."""
        config_data = {
            'version': '1.0',
            'git_integration': {
                'mode': 'track_generated',
                'claude_mention_policy': 'minimal'
            }
        }
        
        config_file = temp_dir / 'enum-test.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        manager = ConfigManager()
        config = manager.load_config(temp_dir)
        
        assert config.git_integration.mode == GitIntegrationMode.TRACK_GENERATED
        assert config.git_integration.claude_mention_policy == ClaudeMentionPolicy.MINIMAL

    def test_invalid_config_file_handling(self, temp_dir):
        """Test handling of invalid configuration files."""
        # Create invalid JSON file
        config_file = temp_dir / 'claude-builder.json'
        config_file.write_text('{ invalid json content }')
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigError, match="Failed to parse configuration file"):
            manager.load_config(temp_dir)

    def test_nonexistent_config_file_handling(self, temp_dir):
        """Test handling when explicitly specified config file doesn't exist."""
        nonexistent_file = temp_dir / 'nonexistent.json'
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigError, match="Configuration file not found"):
            manager.load_config(temp_dir, config_file=nonexistent_file)

    def test_load_config_from_args_helper(self, temp_dir):
        """Test the load_config_from_args helper function."""
        from claude_builder.core.config import load_config_from_args
        
        args = {
            'project_path': str(temp_dir),
            'verbose': True,
            'template': 'test-template'
        }
        
        config = load_config_from_args(args)
        
        assert isinstance(config, Config)
        assert config.user_preferences.prefer_verbose_output is True
        assert 'test-template' in config.templates.preferred_templates


@pytest.mark.unit
@pytest.mark.phase1
class TestConfigIntegration:
    """Test configuration integration with other components."""

    def test_config_with_project_analysis(self, temp_dir, sample_project_path):
        """Test configuration integration with project analysis."""
        # Create config that affects analysis
        config_data = {
            'analysis': {
                'confidence_threshold': 95,
                'ignore_patterns': ['.git/', 'custom_ignore/'],
                'overrides': {
                    'language': 'python',
                    'framework': 'django'
                }
            }
        }
        
        config_file = temp_dir / 'claude-builder.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        manager = ConfigManager()
        config = manager.load_config(temp_dir)
        
        assert config.analysis.confidence_threshold == 95
        assert 'custom_ignore/' in config.analysis.ignore_patterns
        assert config.analysis.overrides['language'] == 'python'

    def test_config_affects_template_selection(self, temp_dir):
        """Test that configuration affects template selection."""
        config_data = {
            'templates': {
                'preferred_templates': ['custom-python', 'web-api'],
                'search_paths': ['./custom_templates/', '~/.claude-builder/templates/']
            }
        }
        
        config_file = temp_dir / 'claude-builder.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        manager = ConfigManager()
        config = manager.load_config(temp_dir)
        
        assert 'custom-python' in config.templates.preferred_templates
        assert './custom_templates/' in config.templates.search_paths

    def test_config_git_integration_settings(self, temp_dir):
        """Test git integration configuration."""
        config_data = {
            'git_integration': {
                'enabled': True,
                'mode': 'exclude_generated',
                'claude_mention_policy': 'forbidden',
                'backup_before_changes': True,
                'files_to_exclude': ['CLAUDE.md', 'AGENTS.md', 'custom_file.md']
            }
        }
        
        config_file = temp_dir / 'claude-builder.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        manager = ConfigManager()
        config = manager.load_config(temp_dir)
        
        assert config.git_integration.enabled is True
        assert config.git_integration.mode == GitIntegrationMode.EXCLUDE_GENERATED
        assert config.git_integration.claude_mention_policy == ClaudeMentionPolicy.FORBIDDEN
        assert 'custom_file.md' in config.git_integration.files_to_exclude

    def test_config_output_settings(self, temp_dir):
        """Test output configuration settings."""
        config_data = {
            'output': {
                'format': 'zip',
                'backup_existing': False,
                'file_permissions': '0755',
                'validate_generated': True
            }
        }
        
        config_file = temp_dir / 'claude-builder.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        manager = ConfigManager()
        config = manager.load_config(temp_dir)
        
        assert config.output.format == 'zip'
        assert config.output.backup_existing is False
        assert config.output.file_permissions == '0755'

    def test_user_preferences_integration(self, temp_dir):
        """Test user preferences configuration."""
        config_data = {
            'user_preferences': {
                'default_editor': 'vim',
                'prefer_verbose_output': True,
                'auto_open_generated_files': True,
                'confirmation_prompts': False
            }
        }
        
        config_file = temp_dir / 'claude-builder.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        manager = ConfigManager()
        config = manager.load_config(temp_dir)
        
        assert config.user_preferences.default_editor == 'vim'
        assert config.user_preferences.prefer_verbose_output is True
        assert config.user_preferences.auto_open_generated_files is True
        assert config.user_preferences.confirmation_prompts is False