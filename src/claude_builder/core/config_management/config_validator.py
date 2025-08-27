"""Configuration validator for schema checking and validation."""

from typing import Any, List, Optional

from claude_builder.utils.exceptions import ConfigError


# Constants imported from parent module
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


class ConfigValidator:
    """Handles configuration validation and schema checking."""

    def __init__(self, schema_version: str = "1.0") -> None:
        self.schema_version = schema_version

    def validate_config(self, config: Any) -> None:
        """Validate configuration object."""
        # Validate version compatibility
        if config.version != self.schema_version:
            msg = f"{UNSUPPORTED_CONFIG_VERSION}: {config.version}"
            raise ConfigError(msg)

        # Validate analysis config
        self._validate_analysis_config(config.analysis)

        # Validate template config
        self._validate_template_config(config.templates)

        # Validate agent config
        self._validate_agent_config(config.agents)

        # Validate output config
        self._validate_output_config(config.output)

        # Validate user preferences
        self._validate_user_preferences(config.user_preferences)

    def _validate_analysis_config(self, analysis: Any) -> None:
        """Validate analysis configuration."""
        if not (0 <= analysis.confidence_threshold <= 100):
            raise ConfigError(CONFIDENCE_THRESHOLD_ERROR)

        if analysis.max_file_size < 1024:
            raise ConfigError(MAX_FILE_SIZE_ERROR)

    def _validate_template_config(self, templates: Any) -> None:
        """Validate template configuration."""
        if templates.template_cache_ttl < 0:
            raise ConfigError(TEMPLATE_CACHE_TTL_ERROR)

    def _validate_agent_config(self, agents: Any) -> None:
        """Validate agent configuration."""
        if agents.max_concurrent_agents < 1:
            raise ConfigError(MAX_CONCURRENT_AGENTS_ERROR)

        if agents.agent_timeout < 30:
            raise ConfigError(AGENT_TIMEOUT_ERROR)

        valid_algorithms = ["intelligent", "strict", "permissive"]
        if agents.agent_selection_algorithm not in valid_algorithms:
            raise ConfigError(INVALID_AGENT_SELECTION_ALGORITHM)

    def _validate_output_config(self, output: Any) -> None:
        """Validate output configuration."""
        # Validate file permissions format (octal format)
        try:
            int(output.file_permissions, 8)
        except ValueError as e:
            raise ConfigError(INVALID_FILE_PERMISSIONS_FORMAT) from e

    def _validate_user_preferences(self, preferences: Any) -> None:
        """Validate user preferences."""
        valid_themes = ["light", "dark", "auto"]
        if preferences.theme not in valid_themes:
            raise ConfigError(INVALID_THEME)

        valid_frequencies = ["never", "daily", "weekly", "monthly"]
        if preferences.update_check_frequency not in valid_frequencies:
            raise ConfigError(INVALID_UPDATE_CHECK_FREQUENCY)

    def validate_config_compatibility(
        self, config: Any, project_analysis: Optional[Any] = None
    ) -> List[str]:
        """Validate configuration compatibility with project."""
        warnings: List[str] = []

        if project_analysis is None:
            return warnings

        # Check for language-specific configurations
        if hasattr(project_analysis, "primary_language"):
            primary_lang = project_analysis.primary_language.lower()

            # Language-specific validation
            if primary_lang == "python" and not any(
                "python" in pattern.lower()
                for pattern in config.analysis.ignore_patterns
            ):
                warnings.append(
                    "Consider adding Python-specific ignore patterns like __pycache__/, *.pyc"
                )

            if primary_lang == "javascript" and not any(
                "node_modules" in pattern.lower()
                for pattern in config.analysis.ignore_patterns
            ):
                warnings.append(
                    "Consider adding JavaScript-specific ignore patterns like node_modules/"
                )

            if primary_lang == "rust" and not any(
                "target" in pattern.lower()
                for pattern in config.analysis.ignore_patterns
            ):
                warnings.append(
                    "Consider adding Rust-specific ignore patterns like target/"
                )

        # Check template compatibility
        if hasattr(project_analysis, "framework") and project_analysis.framework:
            framework = project_analysis.framework.lower()
            if framework not in [
                t.lower() for t in config.templates.preferred_templates
            ]:
                warnings.append(
                    f"Consider adding {framework} to preferred templates for better generation"
                )

        # Check agent configuration against project complexity
        if hasattr(project_analysis, "complexity_score"):
            complexity = project_analysis.complexity_score
            if complexity > 80 and config.agents.max_concurrent_agents < 3:
                warnings.append(
                    "High complexity project detected. Consider increasing max_concurrent_agents"
                )

        return warnings
