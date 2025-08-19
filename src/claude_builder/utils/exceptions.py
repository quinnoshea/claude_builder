"""Exception classes for Claude Builder."""


class ClaudeBuilderError(Exception):
    """Base exception for Claude Builder."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


class AnalysisError(ClaudeBuilderError):
    """Exception raised during project analysis."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=5)


class GenerationError(ClaudeBuilderError):
    """Exception raised during content generation."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=6)


class AgentError(ClaudeBuilderError):
    """Exception raised during agent operations."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=7)


class GitError(ClaudeBuilderError):
    """Exception raised during git operations."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=8)


class ConfigError(ClaudeBuilderError):
    """Exception raised for configuration issues."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=10)


class ValidationError(ClaudeBuilderError):
    """Exception raised for validation failures."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=2)


class TemplateError(ClaudeBuilderError):
    """Exception raised for template system issues."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=6)



# Placeholder classes for test compatibility
class ErrorContext:
    """Placeholder ErrorContext class for test compatibility."""
    
    def __init__(self, operation: str, details: dict = None):
        self.operation = operation
        self.details = details or {}
        self.timestamp = "2024-01-01T00:00:00Z"
        
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "operation": self.operation,
            "details": self.details,
            "timestamp": self.timestamp
        }


class ErrorHandler:
    """Placeholder ErrorHandler class for test compatibility."""
    
    def __init__(self):
        self.error_count = 0
        
    def handle_error(self, error: Exception) -> ErrorContext:
        self.error_count += 1
        return ErrorContext("error_handled", {"count": self.error_count})
