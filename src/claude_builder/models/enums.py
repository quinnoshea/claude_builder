"""Enums compatibility layer.

This module re-exports enum classes from ``claude_builder.core.models`` to
preserve backward compatibility with older imports:

    from claude_builder.models.enums import ProjectType

"""

from claude_builder.core.models import (
    ArchitecturePattern,
    ClaudeMentionPolicy,
    ComplexityLevel,
    GitIntegrationMode,
    ProjectType,
)

__all__ = [
    "ArchitecturePattern",
    "ClaudeMentionPolicy",
    "ComplexityLevel",
    "GitIntegrationMode",
    "ProjectType",
]
