"""Enums compatibility layer.

This module re-exports enum classes from ``claude_builder.core.models`` to
preserve backward compatibility with older imports:

    from claude_builder.models.enums import ProjectType

"""

from claude_builder.core.models import (
    ProjectType,
    ComplexityLevel,
    ArchitecturePattern,
    ClaudeMentionPolicy,
    GitIntegrationMode,
)

__all__ = [
    "ProjectType",
    "ComplexityLevel",
    "ArchitecturePattern",
    "ClaudeMentionPolicy",
    "GitIntegrationMode",
]
