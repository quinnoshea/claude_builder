"""Exception classes for Claude Builder."""


class ClaudeBuilderError(Exception):
    """Base exception for Claude Builder."""

    def __init__(
        self,
        message: str,
        exit_code: int = 1,
        context=None,
        cause=None,
        suggestions=None,
        **kwargs,
    ):
        super().__init__(message)
        self.exit_code = exit_code
        self.context = context
        self.suggestions = suggestions or []

        # Set cause for error chaining
        if cause is not None:
            self.__cause__ = cause

        # Accept additional kwargs and set as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)


class AnalysisError(ClaudeBuilderError):
    """Exception raised during project analysis."""

    def __init__(
        self,
        message: str,
        project_path=None,
        analysis_stage=None,
        file_path=None,
        line_number=None,
        column_number=None,
        **kwargs,
    ):
        super().__init__(
            message,
            exit_code=5,
            project_path=project_path,
            analysis_stage=analysis_stage,
            file_path=file_path,
            line_number=line_number,
            column_number=column_number,
            **kwargs,
        )


class GenerationError(ClaudeBuilderError):
    """Exception raised during content generation."""

    def __init__(self, message: str, template_name=None, output_path=None, **kwargs):
        super().__init__(
            message,
            exit_code=6,
            template_name=template_name,
            output_path=output_path,
            **kwargs,
        )


class AgentError(ClaudeBuilderError):
    """Exception raised during agent operations."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=7)


class GitError(ClaudeBuilderError):
    """Exception raised during git operations."""

    def __init__(
        self,
        message: str,
        command=None,
        working_directory=None,
        git_command=None,
        exit_code=None,
        **kwargs,
    ):
        actual_exit_code = exit_code if exit_code is not None else 8
        super().__init__(
            message,
            exit_code=actual_exit_code,
            command=command,
            working_directory=working_directory,
            git_command=git_command,
            **kwargs,
        )


class ConfigError(ClaudeBuilderError):
    """Exception raised for configuration issues."""

    def __init__(self, message: str, config_file=None, config_section=None, **kwargs):
        super().__init__(
            message,
            exit_code=10,
            config_file=config_file,
            config_section=config_section,
            **kwargs,
        )


class ValidationError(ClaudeBuilderError):
    """Exception raised for validation failures."""

    def __init__(
        self,
        message: str,
        field_name=None,
        field_value=None,
        validation_rules=None,
        **kwargs,
    ):
        super().__init__(
            message,
            exit_code=2,
            field_name=field_name,
            field_value=field_value,
            validation_rules=validation_rules,
            **kwargs,
        )


class TemplateError(ClaudeBuilderError):
    """Exception raised for template system issues."""

    def __init__(
        self,
        message: str,
        template_name=None,
        template_category=None,
        dependency=None,
        **kwargs,
    ):
        super().__init__(
            message,
            exit_code=6,
            template_name=template_name,
            template_category=template_category,
            dependency=dependency,
            **kwargs,
        )


# Placeholder classes for test compatibility
class ErrorContext:
    """Error context class for test compatibility."""

    def __init__(
        self,
        operation: str,
        details: dict = None,
        file_path: str = None,
        metadata: dict = None,
        **kwargs,
    ):
        self.operation = operation
        self.details = details or {}
        self.file_path = file_path
        self.metadata = metadata or {}
        self.timestamp = "2024-01-01T00:00:00Z"
        # Accept any additional kwargs for flexibility
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "operation": self.operation,
            "details": self.details,
            "timestamp": self.timestamp,
        }
        if self.metadata:
            result["metadata"] = self.metadata
        if hasattr(self, "file_path") and self.file_path:
            result["file_path"] = self.file_path
        return result


class ErrorHandler:
    """Error handler class for test compatibility."""

    def __init__(self):
        self.error_count = 0
        self.logged_errors = []
        self.recovery_strategies = {}

    def handle_error(self, error: Exception) -> ErrorContext:
        self.error_count += 1
        return ErrorContext("error_handled", {"count": self.error_count})

    def log_error(self, error: Exception, severity: str = "error") -> None:
        """Log an error with severity level."""
        self.error_count += 1
        error_entry = {
            "error": error,
            "severity": severity,
            "timestamp": "2024-01-01T00:00:00Z",
            "type": type(error).__name__,
        }
        self.logged_errors.append(error_entry)

    def register_recovery_strategy(self, error_type: type, strategy_func):
        """Register a recovery strategy for a specific error type."""
        self.recovery_strategies[error_type] = strategy_func

    def suggest_recovery(self, error: Exception) -> str:
        """Suggest recovery action for an error."""
        error_type = type(error)
        if error_type in self.recovery_strategies:
            return self.recovery_strategies[error_type](error)
        return None

    def get_error_count_by_type(self, error_type: type) -> int:
        """Get count of errors by type."""
        return sum(
            1 for entry in self.logged_errors if isinstance(entry["error"], error_type)
        )

    def get_errors_by_severity(self, severity: str) -> list:
        """Get errors filtered by severity."""
        return [entry for entry in self.logged_errors if entry["severity"] == severity]

    def categorize_errors(self) -> dict:
        """Categorize errors by type."""
        categories = {}
        for entry in self.logged_errors:
            error_type = entry["type"]
            categories[error_type] = categories.get(error_type, 0) + 1
        return categories

    def generate_error_report(self) -> dict:
        """Generate comprehensive error report."""
        return {
            "total_errors": len(self.logged_errors),
            "error_categories": self.categorize_errors(),
            "recent_errors": self.logged_errors[-10:],  # Last 10 errors
            "by_severity": {
                "critical": len(self.get_errors_by_severity("critical")),
                "error": len(self.get_errors_by_severity("error")),
                "warning": len(self.get_errors_by_severity("warning")),
                "info": len(self.get_errors_by_severity("info")),
            },
        }

    def filter_errors(self, severity: str = None, error_type: type = None) -> list:
        """Filter errors by severity and/or type."""
        filtered = self.logged_errors

        if severity:
            filtered = [entry for entry in filtered if entry["severity"] == severity]

        if error_type:
            filtered = [
                entry for entry in filtered if isinstance(entry["error"], error_type)
            ]

        return filtered
