"""
Unit tests for exception handling utilities.

Tests the custom exceptions and error handling including:
- Custom exception classes
- Error message formatting
- Exception chaining and context
- Error recovery mechanisms
- Logging integration
"""

from claude_builder.utils.exceptions import (
    AnalysisError,
    ClaudeBuilderError,
    ConfigError,
    ErrorContext,
    ErrorHandler,
    GenerationError,
    GitError,
    TemplateError,
    ValidationError,
)


class TestClaudeBuilderError:
    """Test suite for base ClaudeBuilderError class."""

    def test_basic_error_creation(self):
        """Test basic error creation."""
        error = ClaudeBuilderError("Something went wrong")

        assert str(error) == "Something went wrong"
        assert error.args == ("Something went wrong",)

    def test_error_with_context(self):
        """Test error creation with context."""
        context = ErrorContext(
            operation="project_analysis",
            file_path="/path/to/project",
            details={"step": "dependency_analysis"},
        )

        error = ClaudeBuilderError("Analysis failed", context=context)

        assert str(error) == "Analysis failed"
        assert error.context == context
        assert error.context.operation == "project_analysis"

    def test_error_chaining(self):
        """Test error chaining with cause."""
        original_error = ValueError("Invalid input")

        error = ClaudeBuilderError("Processing failed", cause=original_error)

        assert str(error) == "Processing failed"
        assert error.__cause__ == original_error

    def test_error_with_suggestions(self):
        """Test error with suggested solutions."""
        error = ClaudeBuilderError(
            "Configuration file not found",
            suggestions=[
                "Create a claude-builder.toml file in the project root",
                "Specify a custom config file path",
                "Use the default configuration",
            ],
        )

        assert len(error.suggestions) == 3
        assert "claude-builder.toml" in error.suggestions[0]


class TestAnalysisError:
    """Test suite for AnalysisError class."""

    def test_analysis_error_creation(self):
        """Test analysis error creation."""
        error = AnalysisError(
            "Failed to analyze project dependencies",
            project_path="/path/to/project",
            analysis_stage="dependency_resolution",
        )

        assert "Failed to analyze project dependencies" in str(error)
        assert error.project_path == "/path/to/project"
        assert error.analysis_stage == "dependency_resolution"

    def test_analysis_error_with_file_details(self):
        """Test analysis error with specific file details."""
        error = AnalysisError(
            "Invalid pyproject.toml format",
            project_path="/path/to/project",
            file_path="/path/to/project/pyproject.toml",
            line_number=15,
            column_number=8,
        )

        assert error.file_path == "/path/to/project/pyproject.toml"
        assert error.line_number == 15
        assert error.column_number == 8

    def test_analysis_error_recovery_suggestions(self):
        """Test analysis error with recovery suggestions."""
        error = AnalysisError(
            "Dependency conflict detected",
            project_path="/path/to/project",
            suggestions=[
                "Update conflicting dependencies to compatible versions",
                "Use virtual environment to isolate dependencies",
                "Check for alternative packages",
            ],
        )

        assert len(error.suggestions) == 3
        assert "virtual environment" in error.suggestions[1]


class TestGenerationError:
    """Test suite for GenerationError class."""

    def test_generation_error_creation(self):
        """Test generation error creation."""
        error = GenerationError(
            "Failed to generate documentation",
            template_name="python-fastapi",
            output_path="/path/to/output",
        )

        assert "Failed to generate documentation" in str(error)
        assert error.template_name == "python-fastapi"
        assert error.output_path == "/path/to/output"

    def test_template_rendering_error(self):
        """Test template rendering specific error."""
        error = GenerationError(
            "Template variable 'undefined_var' not found",
            template_name="custom-template",
            template_line=25,
            variable_name="undefined_var",
        )

        assert error.template_name == "custom-template"
        assert error.template_line == 25
        assert error.variable_name == "undefined_var"

    def test_output_writing_error(self):
        """Test output writing error."""
        error = GenerationError(
            "Permission denied writing to output directory",
            output_path="/readonly/directory",
            error_type="permission_denied",
        )

        assert error.output_path == "/readonly/directory"
        assert error.error_type == "permission_denied"


class TestConfigError:
    """Test suite for ConfigError class."""

    def test_config_error_creation(self):
        """Test config error creation."""
        error = ConfigError(
            "Invalid configuration value",
            config_key="analysis.depth",
            config_value="invalid_depth",
        )

        assert "Invalid configuration value" in str(error)
        assert error.config_key == "analysis.depth"
        assert error.config_value == "invalid_depth"

    def test_config_validation_error(self):
        """Test config validation error."""
        error = ConfigError(
            "Required configuration key missing",
            config_key="project.name",
            validation_rule="required",
        )

        assert error.config_key == "project.name"
        assert error.validation_rule == "required"

    def test_config_file_error(self):
        """Test config file specific error."""
        error = ConfigError(
            "Configuration file syntax error",
            config_file="/path/to/config.toml",
            line_number=12,
            syntax_error="Invalid TOML syntax",
        )

        assert error.config_file == "/path/to/config.toml"
        assert error.line_number == 12
        assert error.syntax_error == "Invalid TOML syntax"


class TestTemplateError:
    """Test suite for TemplateError class."""

    def test_template_error_creation(self):
        """Test template error creation."""
        error = TemplateError(
            "Template not found",
            template_name="missing-template",
            template_path="/path/to/templates",
        )

        assert "Template not found" in str(error)
        assert error.template_name == "missing-template"
        assert error.template_path == "/path/to/templates"

    def test_template_syntax_error(self):
        """Test template syntax error."""
        error = TemplateError(
            "Invalid Jinja2 syntax",
            template_name="broken-template",
            line_number=10,
            syntax_details="Unexpected end of template",
        )

        assert error.template_name == "broken-template"
        assert error.line_number == 10
        assert error.syntax_details == "Unexpected end of template"

    def test_template_dependency_error(self):
        """Test template dependency error."""
        error = TemplateError(
            "Template dependency not found",
            template_name="child-template",
            parent_template="missing-parent",
            dependency_type="extends",
        )

        assert error.template_name == "child-template"
        assert error.parent_template == "missing-parent"
        assert error.dependency_type == "extends"


class TestGitError:
    """Test suite for GitError class."""

    def test_git_error_creation(self):
        """Test git error creation."""
        error = GitError(
            "Git repository not found",
            repo_path="/path/to/project",
            git_command="git status",
        )

        assert "Git repository not found" in str(error)
        assert error.repo_path == "/path/to/project"
        assert error.git_command == "git status"

    def test_git_command_error(self):
        """Test git command execution error."""
        error = GitError(
            "Git command failed",
            git_command="git log --oneline",
            exit_code=128,
            stderr="fatal: not a git repository",
        )

        assert error.git_command == "git log --oneline"
        assert error.exit_code == 128
        assert "not a git repository" in error.stderr

    def test_git_permission_error(self):
        """Test git permission error."""
        error = GitError(
            "Permission denied accessing git repository",
            repo_path="/restricted/repo",
            error_type="permission_denied",
        )

        assert error.repo_path == "/restricted/repo"
        assert error.error_type == "permission_denied"


class TestValidationError:
    """Test suite for ValidationError class."""

    def test_validation_error_creation(self):
        """Test validation error creation."""
        error = ValidationError(
            "Validation failed",
            field_name="project.name",
            field_value="",
            constraint="non_empty",
        )

        assert "Validation failed" in str(error)
        assert error.field_name == "project.name"
        assert error.field_value == ""
        assert error.constraint == "non_empty"

    def test_validation_error_with_rules(self):
        """Test validation error with specific rules."""
        error = ValidationError(
            "Value does not match pattern",
            field_name="project.version",
            field_value="invalid-version",
            constraint="semantic_version",
            pattern=r"^\d+\.\d+\.\d+$",
        )

        assert error.field_name == "project.version"
        assert error.constraint == "semantic_version"
        assert error.pattern == r"^\d+\.\d+\.\d+$"


class TestErrorContext:
    """Test suite for ErrorContext class."""

    def test_error_context_creation(self):
        """Test error context creation."""
        context = ErrorContext(
            operation="template_rendering",
            timestamp="2024-01-15T10:30:00Z",
            user_id="user123",
            session_id="session456",
        )

        assert context.operation == "template_rendering"
        assert context.timestamp == "2024-01-15T10:30:00Z"
        assert context.user_id == "user123"
        assert context.session_id == "session456"

    def test_error_context_with_details(self):
        """Test error context with additional details."""
        context = ErrorContext(
            operation="project_analysis",
            details={
                "project_path": "/path/to/project",
                "analysis_type": "comprehensive",
                "step": "dependency_resolution",
                "progress": 0.75,
            },
        )

        assert context.operation == "project_analysis"
        assert context.details["project_path"] == "/path/to/project"
        assert context.details["progress"] == 0.75

    def test_error_context_serialization(self):
        """Test error context serialization."""
        context = ErrorContext(
            operation="config_validation",
            details={"config_file": "claude-builder.toml"},
            metadata={"version": "1.0.0"},
        )

        serialized = context.to_dict()

        assert serialized["operation"] == "config_validation"
        assert serialized["details"]["config_file"] == "claude-builder.toml"
        assert serialized["metadata"]["version"] == "1.0.0"


class TestErrorHandler:
    """Test suite for ErrorHandler class."""

    def test_error_handler_initialization(self):
        """Test error handler initialization."""
        handler = ErrorHandler()

        assert handler.error_count == 0
        assert handler.logged_errors == []
        assert handler.recovery_strategies is not None

    def test_error_logging(self):
        """Test error logging functionality."""
        handler = ErrorHandler()

        error = ClaudeBuilderError("Test error")
        handler.log_error(error)

        assert handler.error_count == 1
        assert len(handler.logged_errors) == 1
        assert handler.logged_errors[0]["error"] == error

    def test_error_recovery_strategies(self):
        """Test error recovery strategies."""
        handler = ErrorHandler()

        # Register recovery strategy
        def config_error_recovery(error):
            if isinstance(error, ConfigError):
                return "Use default configuration"
            return None

        handler.register_recovery_strategy(ConfigError, config_error_recovery)

        # Test recovery
        config_error = ConfigError("Invalid config")
        recovery = handler.suggest_recovery(config_error)

        assert recovery == "Use default configuration"

    def test_error_categorization(self):
        """Test error categorization."""
        handler = ErrorHandler()

        errors = [
            AnalysisError("Analysis failed"),
            ConfigError("Config invalid"),
            TemplateError("Template missing"),
            AnalysisError("Another analysis error"),
        ]

        for error in errors:
            handler.log_error(error)

        categories = handler.categorize_errors()

        assert categories["AnalysisError"] == 2
        assert categories["ConfigError"] == 1
        assert categories["TemplateError"] == 1

    def test_error_reporting(self):
        """Test error reporting functionality."""
        handler = ErrorHandler()

        # Log various errors
        handler.log_error(AnalysisError("Analysis failed"))
        handler.log_error(ConfigError("Config error"))

        report = handler.generate_error_report()

        assert report["total_errors"] == 2
        assert "AnalysisError" in report["error_categories"]
        assert "ConfigError" in report["error_categories"]
        assert len(report["recent_errors"]) == 2

    def test_error_filtering(self):
        """Test error filtering functionality."""
        handler = ErrorHandler()

        # Log errors with different severities
        handler.log_error(AnalysisError("Critical analysis error"), severity="critical")
        handler.log_error(ConfigError("Warning config issue"), severity="warning")
        handler.log_error(TemplateError("Info template message"), severity="info")

        critical_errors = handler.filter_errors(severity="critical")
        warning_errors = handler.filter_errors(severity="warning")

        assert len(critical_errors) == 1
        assert len(warning_errors) == 1
        assert isinstance(critical_errors[0]["error"], AnalysisError)
        assert isinstance(warning_errors[0]["error"], ConfigError)
