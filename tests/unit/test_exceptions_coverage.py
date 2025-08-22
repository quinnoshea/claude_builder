"""Comprehensive tests for utils.exceptions module to achieve 100% coverage."""

from claude_builder.utils.exceptions import (
    AgentError,
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


def test_claude_builder_error():
    """Test base ClaudeBuilderError class."""
    error = ClaudeBuilderError("Base error")
    assert str(error) == "Base error"
    assert error.exit_code == 1

    # Test with custom exit code
    error_custom = ClaudeBuilderError("Custom error", exit_code=99)
    assert error_custom.exit_code == 99


def test_analysis_error():
    """Test AnalysisError class."""
    error = AnalysisError("Analysis failed")
    assert str(error) == "Analysis failed"
    assert error.exit_code == 5


def test_generation_error():
    """Test GenerationError class."""
    error = GenerationError("Generation failed")
    assert str(error) == "Generation failed"
    assert error.exit_code == 6


def test_agent_error():
    """Test AgentError class - covers line 30."""
    error = AgentError("Agent operation failed")
    assert str(error) == "Agent operation failed"
    assert error.exit_code == 7


def test_git_error():
    """Test GitError class - covers line 37."""
    error = GitError("Git operation failed")
    assert str(error) == "Git operation failed"
    assert error.exit_code == 8


def test_config_error():
    """Test ConfigError class."""
    error = ConfigError("Config error")
    assert str(error) == "Config error"
    assert error.exit_code == 10


def test_validation_error():
    """Test ValidationError class - covers line 51."""
    error = ValidationError("Validation failed")
    assert str(error) == "Validation failed"
    assert error.exit_code == 2


def test_template_error():
    """Test TemplateError class."""
    error = TemplateError("Template error")
    assert str(error) == "Template error"
    assert error.exit_code == 6


def test_error_context():
    """Test ErrorContext class - covers line 73."""
    # Test with defaults
    context = ErrorContext("test_operation")
    assert context.operation == "test_operation"
    assert context.details == {}
    assert context.timestamp == "2024-01-01T00:00:00Z"

    # Test to_dict method
    result = context.to_dict()
    assert result["operation"] == "test_operation"
    assert result["details"] == {}
    assert result["timestamp"] == "2024-01-01T00:00:00Z"

    # Test with custom details
    context_with_details = ErrorContext("custom_op", {"key": "value"})
    assert context_with_details.details == {"key": "value"}


def test_error_handler():
    """Test ErrorHandler class - covers lines 87-88."""
    handler = ErrorHandler()
    assert handler.error_count == 0

    # Test handle_error method
    test_error = Exception("Test exception")
    context = handler.handle_error(test_error)

    assert handler.error_count == 1
    assert isinstance(context, ErrorContext)
    assert context.operation == "error_handled"
    assert context.details == {"count": 1}

    # Test multiple errors
    handler.handle_error(Exception("Second error"))
    assert handler.error_count == 2
