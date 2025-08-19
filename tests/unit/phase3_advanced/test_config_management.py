"""
Unit tests for advanced configuration management components.

Tests the sophisticated configuration system including:
- Multi-environment configuration management
- Configuration validation and schema enforcement
- Dynamic configuration updates
- Configuration inheritance and composition
- Secure configuration handling
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from claude_builder.core.config import (
    AdvancedConfigManager, ConfigSchema, ConfigEnvironment,
    ConfigValidator, SecureConfigHandler, ConfigWatcher
)


class TestConfigSchema:
    """Test suite for ConfigSchema class."""
    
    def test_schema_definition(self):
        """Test configuration schema definition."""
        schema = ConfigSchema()
        
        # Define schema structure
        schema.define_field("project.name", str, required=True)
        schema.define_field("project.version", str, default="0.1.0")
        schema.define_field("analysis.depth", str, choices=["basic", "standard", "detailed"])
        schema.define_field("generation.output_format", str, choices=["markdown", "html", "json"])
        schema.define_field("performance.cache_size", int, min_value=1, max_value=1000)
        
        assert schema.has_field("project.name")
        assert schema.get_field_type("project.name") == str
        assert schema.is_required("project.name")
        assert schema.get_default("project.version") == "0.1.0"
        assert schema.get_choices("analysis.depth") == ["basic", "standard", "detailed"]
    
    def test_schema_validation_success(self):
        """Test successful schema validation."""
        schema = ConfigSchema()
        schema.define_field("project.name", str, required=True)
        schema.define_field("project.type", str, choices=["python", "rust", "javascript"])
        schema.define_field("analysis.include_tests", bool, default=True)
        
        config_data = {
            "project": {
                "name": "test-project",
                "type": "python"
            },
            "analysis": {
                "include_tests": False
            }
        }
        
        validation_result = schema.validate(config_data)
        assert validation_result.is_valid
        assert len(validation_result.errors) == 0
    
    def test_schema_validation_errors(self):
        """Test schema validation with errors."""
        schema = ConfigSchema()
        schema.define_field("project.name", str, required=True)
        schema.define_field("project.type", str, choices=["python", "rust", "javascript"])
        schema.define_field("performance.threads", int, min_value=1, max_value=16)
        
        config_data = {
            "project": {
                "type": "invalid_type"  # Missing required name, invalid choice
            },
            "performance": {
                "threads": 20  # Exceeds max_value
            }
        }
        
        validation_result = schema.validate(config_data)
        assert not validation_result.is_valid
        assert len(validation_result.errors) >= 3
        
        error_messages = [error.message for error in validation_result.errors]
        assert any("project.name" in msg and "required" in msg for msg in error_messages)
        assert any("project.type" in msg and "invalid choice" in msg for msg in error_messages)
        assert any("performance.threads" in msg and "maximum" in msg for msg in error_messages)
    
    def test_schema_nested_validation(self):
        """Test validation of nested configuration structures."""
        schema = ConfigSchema()
        schema.define_field("database.host", str, required=True)
        schema.define_field("database.port", int, min_value=1, max_value=65535)
        schema.define_field("database.credentials.username", str, required=True)
        schema.define_field("database.credentials.password", str, required=True, sensitive=True)
        
        config_data = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {
                    "username": "admin",
                    "password": "secret123"
                }
            }
        }
        
        validation_result = schema.validate(config_data)
        assert validation_result.is_valid
        
        # Test with invalid nested data
        invalid_config = {
            "database": {
                "host": "localhost",
                "port": 70000,  # Invalid port
                "credentials": {
                    "username": "admin"
                    # Missing password
                }
            }
        }
        
        invalid_result = schema.validate(invalid_config)
        assert not invalid_result.is_valid
        assert len(invalid_result.errors) >= 2


class TestConfigEnvironment:
    """Test suite for ConfigEnvironment class."""
    
    def test_environment_creation(self):
        """Test configuration environment creation."""
        env = ConfigEnvironment(
            name="development",
            description="Development environment configuration",
            priority=1
        )
        
        assert env.name == "development"
        assert env.description == "Development environment configuration"
        assert env.priority == 1
        assert env.config_data == {}
    
    def test_environment_configuration_management(self):
        """Test environment-specific configuration management."""
        dev_env = ConfigEnvironment("development")
        prod_env = ConfigEnvironment("production")
        
        # Set environment-specific configurations
        dev_env.set_config({
            "debug": True,
            "database": {
                "host": "localhost",
                "name": "dev_db"
            },
            "logging": {
                "level": "DEBUG"
            }
        })
        
        prod_env.set_config({
            "debug": False,
            "database": {
                "host": "prod-db.example.com",
                "name": "prod_db"
            },
            "logging": {
                "level": "WARNING"
            }
        })
        
        assert dev_env.get_config("debug") is True
        assert prod_env.get_config("debug") is False
        assert dev_env.get_config("database.host") == "localhost"
        assert prod_env.get_config("database.host") == "prod-db.example.com"
    
    def test_environment_inheritance(self):
        """Test configuration inheritance between environments."""
        base_env = ConfigEnvironment("base")
        base_env.set_config({
            "app": {
                "name": "claude-builder",
                "version": "1.0.0"
            },
            "features": {
                "analytics": True,
                "caching": True
            }
        })
        
        dev_env = ConfigEnvironment("development", parent=base_env)
        dev_env.set_config({
            "app": {
                "debug": True  # Additional field
            },
            "features": {
                "analytics": False  # Override
            }
        })
        
        # Should inherit from base and override/add as needed
        merged_config = dev_env.get_merged_config()
        assert merged_config["app"]["name"] == "claude-builder"  # Inherited
        assert merged_config["app"]["version"] == "1.0.0"  # Inherited
        assert merged_config["app"]["debug"] is True  # Added
        assert merged_config["features"]["analytics"] is False  # Overridden
        assert merged_config["features"]["caching"] is True  # Inherited
    
    def test_environment_variable_substitution(self):
        """Test environment variable substitution in configuration."""
        import os
        
        # Set test environment variables
        with patch.dict(os.environ, {
            'DB_HOST': 'test-db-host',
            'DB_PORT': '5432',
            'API_KEY': 'secret-api-key'
        }):
            env = ConfigEnvironment("test")
            env.set_config({
                "database": {
                    "host": "${DB_HOST}",
                    "port": "${DB_PORT}",
                    "url": "postgresql://${DB_HOST}:${DB_PORT}/mydb"
                },
                "api": {
                    "key": "${API_KEY}"
                }
            })
            
            resolved_config = env.resolve_variables()
            assert resolved_config["database"]["host"] == "test-db-host"
            assert resolved_config["database"]["port"] == "5432"
            assert resolved_config["database"]["url"] == "postgresql://test-db-host:5432/mydb"
            assert resolved_config["api"]["key"] == "secret-api-key"


class TestConfigValidator:
    """Test suite for ConfigValidator class."""
    
    def test_validator_initialization(self):
        """Test config validator initialization."""
        schema = ConfigSchema()
        validator = ConfigValidator(schema)
        
        assert validator.schema == schema
        assert validator.validation_rules == []
    
    def test_custom_validation_rules(self):
        """Test custom validation rules."""
        schema = ConfigSchema()
        validator = ConfigValidator(schema)
        
        # Add custom validation rule
        def validate_database_connection(config):
            db_config = config.get("database", {})
            if db_config.get("type") == "postgresql":
                if not db_config.get("host") or not db_config.get("port"):
                    return False, "PostgreSQL requires host and port"
            return True, None
        
        validator.add_rule("database_connection", validate_database_connection)
        
        # Test valid configuration
        valid_config = {
            "database": {
                "type": "postgresql",
                "host": "localhost",
                "port": 5432
            }
        }
        
        result = validator.validate(valid_config)
        assert result.is_valid
        
        # Test invalid configuration
        invalid_config = {
            "database": {
                "type": "postgresql"
                # Missing host and port
            }
        }
        
        result = validator.validate(invalid_config)
        assert not result.is_valid
        assert any("PostgreSQL requires host and port" in error.message for error in result.errors)
    
    def test_conditional_validation(self):
        """Test conditional validation based on other config values."""
        schema = ConfigSchema()
        validator = ConfigValidator(schema)
        
        # Add conditional rule
        def validate_ssl_config(config):
            if config.get("server", {}).get("use_ssl"):
                ssl_config = config.get("ssl", {})
                if not ssl_config.get("cert_file") or not ssl_config.get("key_file"):
                    return False, "SSL enabled but cert_file or key_file missing"
            return True, None
        
        validator.add_rule("ssl_conditional", validate_ssl_config)
        
        # Test SSL enabled with proper config
        valid_ssl_config = {
            "server": {"use_ssl": True},
            "ssl": {
                "cert_file": "/path/to/cert.pem",
                "key_file": "/path/to/key.pem"
            }
        }
        
        result = validator.validate(valid_ssl_config)
        assert result.is_valid
        
        # Test SSL enabled without proper config
        invalid_ssl_config = {
            "server": {"use_ssl": True},
            "ssl": {}
        }
        
        result = validator.validate(invalid_ssl_config)
        assert not result.is_valid
    
    def test_cross_field_validation(self):
        """Test validation that involves multiple configuration fields."""
        schema = ConfigSchema()
        validator = ConfigValidator(schema)
        
        # Add cross-field validation
        def validate_performance_settings(config):
            perf = config.get("performance", {})
            cache_size = perf.get("cache_size", 0)
            max_workers = perf.get("max_workers", 1)
            
            # Cache size should be proportional to workers
            if cache_size > 0 and max_workers > 1:
                min_cache_per_worker = 10
                if cache_size < (max_workers * min_cache_per_worker):
                    return False, f"Cache size too small for {max_workers} workers. Minimum: {max_workers * min_cache_per_worker}"
            
            return True, None
        
        validator.add_rule("performance_balance", validate_performance_settings)
        
        # Test balanced configuration
        balanced_config = {
            "performance": {
                "cache_size": 100,
                "max_workers": 4
            }
        }
        
        result = validator.validate(balanced_config)
        assert result.is_valid
        
        # Test unbalanced configuration
        unbalanced_config = {
            "performance": {
                "cache_size": 20,
                "max_workers": 8
            }
        }
        
        result = validator.validate(unbalanced_config)
        assert not result.is_valid


class TestSecureConfigHandler:
    """Test suite for SecureConfigHandler class."""
    
    def test_secure_handler_initialization(self):
        """Test secure config handler initialization."""
        handler = SecureConfigHandler(encryption_key="test-key-123")
        
        assert handler.encryption_key == "test-key-123"
        assert handler.encrypted_fields == set()
    
    def test_sensitive_field_identification(self):
        """Test identification and handling of sensitive fields."""
        handler = SecureConfigHandler()
        
        config = {
            "database": {
                "host": "localhost",
                "password": "secret123",
                "api_key": "key-456"
            },
            "auth": {
                "jwt_secret": "jwt-secret-789",
                "username": "admin"
            }
        }
        
        # Should identify sensitive fields
        sensitive_fields = handler.identify_sensitive_fields(config)
        
        assert "database.password" in sensitive_fields
        assert "database.api_key" in sensitive_fields
        assert "auth.jwt_secret" in sensitive_fields
        assert "database.host" not in sensitive_fields
        assert "auth.username" not in sensitive_fields
    
    def test_configuration_encryption(self):
        """Test configuration encryption and decryption."""
        handler = SecureConfigHandler(encryption_key="test-encryption-key")
        
        config = {
            "database": {
                "host": "localhost",
                "password": "supersecret",
                "port": 5432
            },
            "api": {
                "key": "api-secret-key"
            }
        }
        
        # Mark sensitive fields
        handler.mark_sensitive("database.password")
        handler.mark_sensitive("api.key")
        
        # Encrypt configuration
        encrypted_config = handler.encrypt_config(config)
        
        # Sensitive fields should be encrypted
        assert encrypted_config["database"]["password"] != "supersecret"
        assert encrypted_config["api"]["key"] != "api-secret-key"
        # Non-sensitive fields should remain unchanged
        assert encrypted_config["database"]["host"] == "localhost"
        assert encrypted_config["database"]["port"] == 5432
        
        # Decrypt configuration
        decrypted_config = handler.decrypt_config(encrypted_config)
        
        # Should match original
        assert decrypted_config["database"]["password"] == "supersecret"
        assert decrypted_config["api"]["key"] == "api-secret-key"
        assert decrypted_config["database"]["host"] == "localhost"
    
    def test_secure_storage_integration(self, temp_dir):
        """Test integration with secure storage backends."""
        handler = SecureConfigHandler()
        
        # Mock secure storage backend
        with patch('claude_builder.core.config.KeyVault') as mock_vault:
            mock_vault_instance = MagicMock()
            mock_vault_instance.store_secret.return_value = "secret-id-123"
            mock_vault_instance.retrieve_secret.return_value = "retrieved-secret"
            mock_vault.return_value = mock_vault_instance
            
            # Store secret
            secret_id = handler.store_secret("database.password", "supersecret")
            assert secret_id == "secret-id-123"
            
            # Retrieve secret
            retrieved = handler.retrieve_secret(secret_id)
            assert retrieved == "retrieved-secret"
            
            mock_vault_instance.store_secret.assert_called_once_with("supersecret")
            mock_vault_instance.retrieve_secret.assert_called_once_with("secret-id-123")
    
    def test_configuration_masking(self):
        """Test configuration masking for logging and display."""
        handler = SecureConfigHandler()
        
        config = {
            "database": {
                "host": "localhost",
                "username": "admin",
                "password": "supersecret123",
                "port": 5432
            },
            "api": {
                "endpoint": "https://api.example.com",
                "key": "very-secret-api-key"
            }
        }
        
        # Mark sensitive fields
        handler.mark_sensitive("database.password")
        handler.mark_sensitive("api.key")
        
        # Mask configuration
        masked_config = handler.mask_config(config)
        
        # Sensitive fields should be masked
        assert masked_config["database"]["password"] == "***"
        assert masked_config["api"]["key"] == "***"
        # Non-sensitive fields should remain unchanged
        assert masked_config["database"]["host"] == "localhost"
        assert masked_config["database"]["username"] == "admin"
        assert masked_config["api"]["endpoint"] == "https://api.example.com"


class TestConfigWatcher:
    """Test suite for ConfigWatcher class."""
    
    def test_watcher_initialization(self, temp_dir):
        """Test config watcher initialization."""
        config_file = temp_dir / "config.toml"
        watcher = ConfigWatcher(config_file)
        
        assert watcher.config_file == config_file
        assert watcher.callbacks == []
        assert watcher.last_modified is None
    
    def test_configuration_change_detection(self, temp_dir):
        """Test detection of configuration file changes."""
        config_file = temp_dir / "config.toml"
        config_file.write_text("""
[project]
name = "test"
version = "1.0.0"
""")
        
        watcher = ConfigWatcher(config_file)
        
        # Register callback
        callback_called = []
        def on_config_change(old_config, new_config):
            callback_called.append((old_config, new_config))
        
        watcher.add_callback(on_config_change)
        
        # Simulate initial load
        watcher.start_watching()
        
        # Modify configuration
        config_file.write_text("""
[project]
name = "test"
version = "2.0.0"
""")
        
        # Simulate file change detection
        watcher._check_for_changes()
        
        # Callback should have been called
        assert len(callback_called) > 0
    
    def test_hot_reload_functionality(self, temp_dir):
        """Test hot reload functionality."""
        config_file = temp_dir / "config.toml"
        config_file.write_text("""
[server]
port = 8000
debug = false
""")
        
        watcher = ConfigWatcher(config_file)
        
        # Mock application configuration
        app_config = {"server": {"port": 8000, "debug": False}}
        
        def reload_app_config(old_config, new_config):
            app_config.update(new_config)
        
        watcher.add_callback(reload_app_config)
        watcher.start_watching()
        
        # Simulate configuration change
        config_file.write_text("""
[server]
port = 9000
debug = true
""")
        
        watcher._check_for_changes()
        
        # Application config should be updated
        assert app_config["server"]["port"] == 9000
        assert app_config["server"]["debug"] is True
    
    def test_validation_on_change(self, temp_dir):
        """Test configuration validation on file changes."""
        config_file = temp_dir / "config.toml"
        config_file.write_text("""
[project]
name = "test"
type = "python"
""")
        
        # Create schema for validation
        schema = ConfigSchema()
        schema.define_field("project.name", str, required=True)
        schema.define_field("project.type", str, choices=["python", "rust", "javascript"])
        
        validator = ConfigValidator(schema)
        watcher = ConfigWatcher(config_file, validator=validator)
        
        validation_results = []
        def on_validation_result(is_valid, errors):
            validation_results.append((is_valid, errors))
        
        watcher.add_validation_callback(on_validation_result)
        watcher.start_watching()
        
        # Make valid change
        config_file.write_text("""
[project]
name = "test"
type = "rust"
""")
        
        watcher._check_for_changes()
        
        # Should pass validation
        assert len(validation_results) > 0
        assert validation_results[-1][0] is True  # is_valid
        
        # Make invalid change
        config_file.write_text("""
[project]
name = "test"
type = "invalid_type"
""")
        
        watcher._check_for_changes()
        
        # Should fail validation
        assert validation_results[-1][0] is False  # is_valid
        assert len(validation_results[-1][1]) > 0  # has errors


class TestAdvancedConfigManager:
    """Test suite for AdvancedConfigManager class."""
    
    def test_manager_initialization(self, temp_dir):
        """Test advanced config manager initialization."""
        manager = AdvancedConfigManager(config_directory=temp_dir)
        
        assert manager.config_directory == temp_dir
        assert manager.environments == {}
        assert manager.current_environment is None
        assert manager.schema is not None
    
    def test_multi_environment_management(self, temp_dir):
        """Test managing multiple configuration environments."""
        manager = AdvancedConfigManager(config_directory=temp_dir)
        
        # Create environment configurations
        (temp_dir / "development.toml").write_text("""
[project]
name = "test-project"
debug = true

[database]
host = "localhost"
port = 5432
""")
        
        (temp_dir / "production.toml").write_text("""
[project]
name = "test-project"
debug = false

[database]
host = "prod-db.example.com"
port = 5432
""")
        
        # Load environments
        manager.load_environments()
        
        assert "development" in manager.environments
        assert "production" in manager.environments
        
        # Switch between environments
        manager.activate_environment("development")
        assert manager.get_config("project.debug") is True
        assert manager.get_config("database.host") == "localhost"
        
        manager.activate_environment("production")
        assert manager.get_config("project.debug") is False
        assert manager.get_config("database.host") == "prod-db.example.com"
    
    def test_configuration_composition(self, temp_dir):
        """Test configuration composition from multiple sources."""
        manager = AdvancedConfigManager(config_directory=temp_dir)
        
        # Base configuration
        (temp_dir / "base.toml").write_text("""
[app]
name = "claude-builder"
version = "1.0.0"

[features]
analytics = true
caching = true
""")
        
        # Environment-specific override
        (temp_dir / "development.toml").write_text("""
[app]
debug = true

[features]
analytics = false

[development]
hot_reload = true
""")
        
        # User-specific override
        (temp_dir / "user.toml").write_text("""
[features]
experimental = true

[user]
preferences = "custom"
""")
        
        # Compose configuration
        composed_config = manager.compose_configuration([
            temp_dir / "base.toml",
            temp_dir / "development.toml", 
            temp_dir / "user.toml"
        ])
        
        # Should merge all sources with proper precedence
        assert composed_config["app"]["name"] == "claude-builder"  # From base
        assert composed_config["app"]["version"] == "1.0.0"  # From base
        assert composed_config["app"]["debug"] is True  # From development
        assert composed_config["features"]["analytics"] is False  # Overridden by development
        assert composed_config["features"]["caching"] is True  # From base
        assert composed_config["features"]["experimental"] is True  # From user
        assert composed_config["development"]["hot_reload"] is True  # From development
        assert composed_config["user"]["preferences"] == "custom"  # From user
    
    def test_dynamic_configuration_updates(self, temp_dir):
        """Test dynamic configuration updates at runtime."""
        manager = AdvancedConfigManager(config_directory=temp_dir)
        
        # Initial configuration
        config_file = temp_dir / "runtime.toml"
        config_file.write_text("""
[server]
port = 8000
workers = 4
""")
        
        manager.load_configuration(config_file)
        
        # Update configuration dynamically
        manager.update_config("server.port", 9000)
        manager.update_config("server.max_connections", 1000)  # New field
        
        assert manager.get_config("server.port") == 9000
        assert manager.get_config("server.workers") == 4  # Unchanged
        assert manager.get_config("server.max_connections") == 1000
        
        # Persist changes
        manager.save_configuration(config_file)
        
        # Verify persistence
        reloaded_manager = AdvancedConfigManager(config_directory=temp_dir)
        reloaded_manager.load_configuration(config_file)
        
        assert reloaded_manager.get_config("server.port") == 9000
        assert reloaded_manager.get_config("server.max_connections") == 1000
    
    def test_configuration_profiles(self, temp_dir):
        """Test configuration profiles for different use cases."""
        manager = AdvancedConfigManager(config_directory=temp_dir)
        
        # Create profiles
        profiles = {
            "minimal": {
                "analysis": {"depth": "basic", "include_git": False},
                "generation": {"template_variant": "minimal", "include_agents": False}
            },
            "comprehensive": {
                "analysis": {"depth": "detailed", "include_git": True},
                "generation": {"template_variant": "comprehensive", "include_agents": True}
            },
            "performance": {
                "analysis": {"depth": "standard", "parallel": True},
                "generation": {"template_variant": "optimized", "cache_enabled": True}
            }
        }
        
        for profile_name, config in profiles.items():
            manager.create_profile(profile_name, config)
        
        # Test profile activation
        manager.activate_profile("minimal")
        assert manager.get_config("analysis.depth") == "basic"
        assert manager.get_config("generation.template_variant") == "minimal"
        
        manager.activate_profile("comprehensive")
        assert manager.get_config("analysis.depth") == "detailed"
        assert manager.get_config("generation.include_agents") is True
        
        # Test profile merging
        merged_config = manager.merge_profiles(["minimal", "performance"])
        assert merged_config["analysis"]["depth"] == "standard"  # From performance (later)
        assert merged_config["generation"]["template_variant"] == "optimized"  # From performance
        assert merged_config["generation"]["include_agents"] is False  # From minimal
    
    def test_configuration_migration(self, temp_dir):
        """Test configuration migration between versions."""
        manager = AdvancedConfigManager(config_directory=temp_dir)
        
        # Old configuration format (v1.0)
        old_config = temp_dir / "old_config.toml"
        old_config.write_text("""
version = "1.0"

[project]
name = "test"
type = "python"

[output]
format = "md"
location = "docs/"
""")
        
        # Define migration rules
        migration_rules = {
            "1.0": {
                "2.0": {
                    "rename": {
                        "output.format": "generation.output_format",
                        "output.location": "generation.output_directory"
                    },
                    "transform": {
                        "generation.output_format": lambda x: "markdown" if x == "md" else x
                    },
                    "add": {
                        "generation.template_variant": "comprehensive"
                    }
                }
            }
        }
        
        manager.set_migration_rules(migration_rules)
        
        # Migrate configuration
        migrated_config = manager.migrate_configuration(old_config, target_version="2.0")
        
        # Should have migrated structure
        assert migrated_config["version"] == "2.0"
        assert migrated_config["project"]["name"] == "test"
        assert migrated_config["generation"]["output_format"] == "markdown"  # Transformed
        assert migrated_config["generation"]["output_directory"] == "docs/"  # Renamed
        assert migrated_config["generation"]["template_variant"] == "comprehensive"  # Added
        assert "output" not in migrated_config  # Old section removed