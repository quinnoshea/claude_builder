"""Git integration utilities for Claude Builder."""

import json
import shutil

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from claude_builder.utils.exceptions import GitError


FAILED_TO_ADD_EXCLUDES = "Failed to add excludes"
FAILED_TO_CREATE_BACKUP = "Failed to create backup"
BACKUP_NOT_FOUND = "Backup not found"
BACKUP_METADATA_NOT_FOUND = "Backup metadata not found"
FAILED_TO_RESTORE_BACKUP = "Failed to restore backup"


@dataclass
class GitIntegrationResult:
    """Result of git integration operations."""

    success: bool
    operations_performed: List[str]
    backup_id: Optional[str] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class GitIntegrationManager:
    """Manages git integration features safely."""

    def __init__(self) -> None:
        self.backup_manager = GitBackupManager()
        self.exclude_manager = GitExcludeManager()
        self.hook_manager = GitHookManager()

    def integrate(self, project_path: Path, config: Any) -> GitIntegrationResult:
        """Perform git integration based on configuration."""
        if not config.enabled:
            return GitIntegrationResult(
                success=True, operations_performed=["Git integration disabled"]
            )

        # Validate git repository
        if not self._is_git_repository(project_path):
            return GitIntegrationResult(
                success=False,
                operations_performed=[],
                errors=["Not a git repository"],
            )

        try:
            operations: List[str] = []
            backup_id: Optional[str] = None

            # Create backup if requested
            backup_id = self._handle_backup_creation(config, project_path, operations)

            # Handle file exclusion/tracking
            self._handle_file_mode_operations(config, project_path, operations)

            # Install git hooks for Claude mention control
            self._handle_hook_installation(config, project_path, operations)

            return GitIntegrationResult(
                success=True, operations_performed=operations, backup_id=backup_id
            )

        except GitError:
            raise
        except OSError as e:
            return self._handle_integration_error(e, project_path, backup_id)

    def _handle_backup_creation(
        self, config: Any, project_path: Path, operations: List[str]
    ) -> Optional[str]:
        """Handle backup creation if requested."""
        if not config.backup_before_changes:
            return None
        backup_id = self.backup_manager.create_backup(project_path)
        operations.append(f"Created backup: {backup_id}")
        return backup_id

    def _handle_file_mode_operations(
        self, config: Any, project_path: Path, operations: List[str]
    ) -> None:
        """Handle file exclusion/tracking based on mode."""
        if not hasattr(config, "mode"):
            return

        if config.mode.value == "exclude_generated":
            self._handle_exclude_mode(config, project_path, operations)
        elif config.mode.value == "track_generated":
            self._handle_track_mode(config, project_path, operations)

    def _handle_exclude_mode(
        self, config: Any, project_path: Path, operations: List[str]
    ) -> None:
        """Handle exclude_generated mode."""
        result = self.exclude_manager.add_excludes(
            project_path, config.files_to_exclude
        )
        if result.success:
            operations.append("Added files to .git/info/exclude")
        else:
            error_msg = f"{FAILED_TO_ADD_EXCLUDES}: {result.errors}"
            raise GitError(error_msg)

    def _handle_track_mode(
        self, config: Any, project_path: Path, operations: List[str]
    ) -> None:
        """Handle track_generated mode."""
        result = self.exclude_manager.remove_excludes(
            project_path, config.files_to_exclude
        )
        if result.success:
            operations.append("Removed files from .git/info/exclude")

    def _handle_hook_installation(
        self, config: Any, project_path: Path, operations: List[str]
    ) -> None:
        """Handle git hook installation for Claude mention control."""
        if not (
            hasattr(config, "claude_mention_policy")
            and config.claude_mention_policy.value != "allowed"
        ):
            return

        hook_result = self.hook_manager.install_commit_msg_hook(
            project_path, config.claude_mention_policy
        )
        if hook_result.success:
            operations.extend(hook_result.operations_performed)
        else:
            # Non-fatal error for hooks
            operations.append(
                f"Warning: Failed to install git hooks: {hook_result.errors}"
            )

    def _handle_integration_error(
        self, error: Exception, project_path: Path, backup_id: Optional[str]
    ) -> GitIntegrationResult:
        """Handle integration errors with rollback if needed."""
        if backup_id:
            try:
                self.backup_manager.restore_backup(project_path, backup_id)
            except GitError as rollback_error:
                return GitIntegrationResult(
                    success=False,
                    operations_performed=[],
                    errors=[
                        f"Integration failed: {error}",
                        f"Rollback failed: {rollback_error}",
                    ],
                )

        return GitIntegrationResult(
            success=False, operations_performed=[], errors=[str(error)]
        )

    def _is_git_repository(self, project_path: Path) -> bool:
        """Check if directory is a git repository."""
        return (project_path / ".git").exists()


class GitExcludeManager:
    """Manages .git/info/exclude file modifications."""

    CLAUDE_MARKER_START = "# === Claude Builder Generated Files (START) ==="
    CLAUDE_MARKER_END = "# === Claude Builder Generated Files (END) ==="

    def __init__(self) -> None:
        pass

    def add_excludes(
        self, project_path: Path, files_to_exclude: List[str]
    ) -> GitIntegrationResult:
        """Add files to .git/info/exclude."""
        try:
            exclude_file = project_path / ".git" / "info" / "exclude"

            # Ensure .git/info directory exists
            exclude_file.parent.mkdir(parents=True, exist_ok=True)

            # Read existing content
            existing_content = []
            if exclude_file.exists():
                with exclude_file.open(encoding="utf-8") as f:
                    existing_content = f.read().splitlines()

            # Check if Claude section already exists
            if self._has_claude_section(existing_content):
                return GitIntegrationResult(
                    success=False,
                    operations_performed=[],
                    errors=[
                        "Claude Builder section already exists in .git/info/exclude"
                    ],
                )

            # Add Claude section
            new_content = existing_content + self._create_claude_section(
                files_to_exclude
            )

            # Write back
            with exclude_file.open("w", encoding="utf-8") as f:
                f.write("\n".join(new_content) + "\n")

            return GitIntegrationResult(
                success=True,
                operations_performed=[
                    f"Added {len(files_to_exclude)} patterns to .git/info/exclude"
                ],
            )

        except OSError as e:
            error_msg = f"{FAILED_TO_ADD_EXCLUDES}: {e}"
            return GitIntegrationResult(
                success=False,
                operations_performed=[],
                errors=[error_msg],
            )

    def remove_excludes(
        self, project_path: Path, files_to_exclude: List[str]  # noqa: ARG002
    ) -> GitIntegrationResult:
        """Remove Claude Builder section from .git/info/exclude."""
        try:
            exclude_file = project_path / ".git" / "info" / "exclude"

            if not exclude_file.exists():
                return GitIntegrationResult(
                    success=True,
                    operations_performed=["No .git/info/exclude file found"],
                )

            # Read existing content
            with exclude_file.open(encoding="utf-8") as f:
                lines = f.read().splitlines()

            # Remove Claude section
            new_lines = self._remove_claude_section(lines)

            if len(new_lines) == len(lines):
                return GitIntegrationResult(
                    success=True,
                    operations_performed=["No Claude Builder section found"],
                )

            # Write back
            with exclude_file.open("w", encoding="utf-8") as f:
                f.write("\n".join(new_lines) + "\n")

            return GitIntegrationResult(
                success=True,
                operations_performed=[
                    "Removed Claude Builder section from .git/info/exclude"
                ],
            )

        except OSError as e:
            return GitIntegrationResult(
                success=False,
                operations_performed=[],
                errors=[f"Failed to remove excludes: {e}"],
            )

    def _has_claude_section(self, lines: List[str]) -> bool:
        """Check if Claude Builder section exists."""
        return any(self.CLAUDE_MARKER_START in line for line in lines)

    def _create_claude_section(self, files_to_exclude: List[str]) -> List[str]:
        """Create Claude Builder section for exclude file."""
        section = [
            "",
            self.CLAUDE_MARKER_START,
            f"# Added by Claude Builder on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}",
            "# These files are generated by Claude Builder for development optimization",
            "# Remove this section if you want to track these files in git",
            "",
        ]

        # Add exclude patterns
        for pattern in files_to_exclude:
            section.append(pattern)

        section.extend(["", self.CLAUDE_MARKER_END, ""])

        return section

    def _remove_claude_section(self, lines: List[str]) -> List[str]:
        """Remove Claude Builder section from lines."""
        new_lines = []
        in_claude_section = False

        for line in lines:
            if self.CLAUDE_MARKER_START in line:
                in_claude_section = True
                continue
            if self.CLAUDE_MARKER_END in line:
                in_claude_section = False
                continue
            if not in_claude_section:
                new_lines.append(line)

        return new_lines


class GitBackupManager:
    """Manages backup and restore of git configurations."""

    def __init__(self) -> None:
        pass

    def create_backup(self, project_path: Path) -> str:
        """Create a backup of git configuration files."""
        backup_id = (
            f"claude_builder_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        )
        backup_dir = project_path / ".git" / "claude-builder-backups" / backup_id

        try:
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Files to backup
            files_to_backup = [
                ".git/info/exclude",
                ".git/hooks/commit-msg",
                ".git/hooks/pre-commit",
                ".gitignore",  # In case we modify it in the future
            ]

            backed_up_files = []

            for file_path in files_to_backup:
                source = project_path / file_path
                if source.exists():
                    dest = backup_dir / file_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest)
                    backed_up_files.append(file_path)

            # Create backup metadata
            metadata = {
                "backup_id": backup_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "backed_up_files": backed_up_files,
                "claude_builder_version": "0.1.0",
            }

            with (backup_dir / "metadata.json").open("w") as f:
                json.dump(metadata, f, indent=2)

        except OSError as e:
            error_msg = f"{FAILED_TO_CREATE_BACKUP}: {e}"
            raise GitError(error_msg) from e
        else:
            return backup_id

    def restore_backup(self, project_path: Path, backup_id: str) -> bool:
        """Restore from a backup."""
        backup_dir = project_path / ".git" / "claude-builder-backups" / backup_id

        if not backup_dir.exists():
            error_msg = f"{BACKUP_NOT_FOUND}: {backup_id}"
            raise GitError(error_msg)

        try:
            # Load metadata
            metadata_file = backup_dir / "metadata.json"
            if not metadata_file.exists():
                error_msg = f"{BACKUP_METADATA_NOT_FOUND}: {backup_id}"
                raise GitError(error_msg)

            with metadata_file.open() as f:
                metadata = json.load(f)

            # Restore files
            for file_path in metadata["backed_up_files"]:
                source = backup_dir / file_path
                dest = project_path / file_path

                if source.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest)

        except OSError as e:
            error_msg = f"{FAILED_TO_RESTORE_BACKUP} {backup_id}: {e}"
            raise GitError(error_msg) from e
        else:
            return True

    def list_backups(self, project_path: Path) -> List[Dict[str, Any]]:
        """List available backups."""
        backups_dir = project_path / ".git" / "claude-builder-backups"

        if not backups_dir.exists():
            return []

        backups = []

        for backup_dir in backups_dir.iterdir():
            if backup_dir.is_dir():
                metadata_file = backup_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with metadata_file.open() as f:
                            metadata = json.load(f)
                        backups.append(metadata)
                    except (OSError, json.JSONDecodeError):
                        # Skip corrupted metadata files
                        pass

        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)

    def cleanup_old_backups(self, project_path: Path, keep_count: int = 5) -> int:
        """Clean up old backups, keeping only the most recent ones."""
        backups = self.list_backups(project_path)

        if len(backups) <= keep_count:
            return 0

        backups_to_remove = backups[keep_count:]
        removed_count = 0

        for backup in backups_to_remove:
            backup_dir = (
                project_path / ".git" / "claude-builder-backups" / backup["backup_id"]
            )
            if backup_dir.exists():
                try:
                    shutil.rmtree(backup_dir)
                    removed_count += 1
                except OSError:
                    # Skip if can't remove
                    pass

        return removed_count


class GitHookManager:
    """Manages git hooks for Claude mention control."""

    def __init__(self) -> None:
        pass

    def install_commit_msg_hook(
        self, project_path: Path, claude_mention_policy: Any
    ) -> GitIntegrationResult:
        """Install commit-msg hook to filter Claude mentions."""
        try:
            hooks_dir = project_path / ".git" / "hooks"
            commit_msg_hook = hooks_dir / "commit-msg"

            # Create hooks directory if it doesn't exist
            hooks_dir.mkdir(parents=True, exist_ok=True)

            # Check if hook already exists
            if commit_msg_hook.exists():
                # Check if it's our hook or a different one
                with commit_msg_hook.open(encoding="utf-8") as f:
                    content = f.read()

                if "Claude Builder" in content:
                    return GitIntegrationResult(
                        success=True,
                        operations_performed=["Commit-msg hook already installed"],
                    )
                # Backup existing hook
                backup_hook = commit_msg_hook.with_suffix(".pre-claude-builder")
                shutil.copy2(commit_msg_hook, backup_hook)

                # Chain with existing hook
                hook_content = self._generate_chained_commit_msg_hook(
                    claude_mention_policy, str(backup_hook)
                )
            else:
                # Create new hook
                hook_content = self._generate_commit_msg_hook(claude_mention_policy)

            # Write hook
            with commit_msg_hook.open("w", encoding="utf-8") as f:
                f.write(hook_content)

            # Make executable
            commit_msg_hook.chmod(0o755)

            return GitIntegrationResult(
                success=True,
                operations_performed=[
                    "Installed commit-msg hook for Claude mention filtering"
                ],
            )

        except OSError as e:
            return GitIntegrationResult(
                success=False,
                operations_performed=[],
                errors=[f"Failed to install commit-msg hook: {e}"],
            )

    def install_pre_commit_hook(
        self, project_path: Path, claude_mention_policy: Any
    ) -> GitIntegrationResult:
        """Install pre-commit hook for additional Claude mention filtering."""
        try:
            hooks_dir = project_path / ".git" / "hooks"
            pre_commit_hook = hooks_dir / "pre-commit"

            # Create hooks directory if it doesn't exist
            hooks_dir.mkdir(parents=True, exist_ok=True)

            # Check if hook already exists
            if pre_commit_hook.exists():
                with pre_commit_hook.open(encoding="utf-8") as f:
                    content = f.read()

                if "Claude Builder" in content:
                    return GitIntegrationResult(
                        success=True,
                        operations_performed=["Pre-commit hook already installed"],
                    )
                # Backup existing hook
                backup_hook = pre_commit_hook.with_suffix(".pre-claude-builder")
                shutil.copy2(pre_commit_hook, backup_hook)

                # Chain with existing hook
                hook_content = self._generate_chained_pre_commit_hook(
                    claude_mention_policy, str(backup_hook)
                )
            else:
                # Create new hook
                hook_content = self._generate_pre_commit_hook(claude_mention_policy)

            # Write hook
            with pre_commit_hook.open("w", encoding="utf-8") as f:
                f.write(hook_content)

            # Make executable
            pre_commit_hook.chmod(0o755)

            return GitIntegrationResult(
                success=True,
                operations_performed=[
                    "Installed pre-commit hook for Claude mention filtering"
                ],
            )

        except OSError as e:
            return GitIntegrationResult(
                success=False,
                operations_performed=[],
                errors=[f"Failed to install pre-commit hook: {e}"],
            )

    def uninstall_hooks(self, project_path: Path) -> GitIntegrationResult:
        """Uninstall Claude Builder git hooks."""
        try:
            hooks_dir = project_path / ".git" / "hooks"
            operations = []

            # Remove or restore commit-msg hook
            commit_msg_hook = hooks_dir / "commit-msg"
            commit_msg_backup = hooks_dir / "commit-msg.pre-claude-builder"

            if commit_msg_hook.exists():
                with commit_msg_hook.open(encoding="utf-8") as f:
                    content = f.read()

                if "Claude Builder" in content:
                    if commit_msg_backup.exists():
                        # Restore original hook
                        shutil.move(commit_msg_backup, commit_msg_hook)
                        operations.append("Restored original commit-msg hook")
                    else:
                        # Remove our hook
                        commit_msg_hook.unlink()
                        operations.append("Removed commit-msg hook")

            # Remove or restore pre-commit hook
            pre_commit_hook = hooks_dir / "pre-commit"
            pre_commit_backup = hooks_dir / "pre-commit.pre-claude-builder"

            if pre_commit_hook.exists():
                with pre_commit_hook.open(encoding="utf-8") as f:
                    content = f.read()

                if "Claude Builder" in content:
                    if pre_commit_backup.exists():
                        # Restore original hook
                        shutil.move(pre_commit_backup, pre_commit_hook)
                        operations.append("Restored original pre-commit hook")
                    else:
                        # Remove our hook
                        pre_commit_hook.unlink()
                        operations.append("Removed pre-commit hook")

            if not operations:
                operations.append("No Claude Builder hooks found to remove")

            return GitIntegrationResult(success=True, operations_performed=operations)

        except OSError as e:
            return GitIntegrationResult(
                success=False,
                operations_performed=[],
                errors=[f"Failed to uninstall hooks: {e}"],
            )

    def _generate_commit_msg_hook(self, claude_mention_policy: Any) -> str:
        """Generate commit-msg hook script."""
        policy_value = claude_mention_policy.value

        return f"""#!/bin/sh
# Claude Builder commit-msg hook
# Policy: {policy_value}
# Filters Claude/AI references from commit messages

COMMIT_FILE="$1"
TEMP_FILE=$(mktemp)

# Read the commit message
commit_msg=$(cat "$COMMIT_FILE")

# Apply filtering based on policy
if [ "{policy_value}" = "forbidden" ]; then
    # Remove all Claude/AI mentions
    echo "$commit_msg" | \\
        sed 's/\\bClaude\\b/AI assistant/gi' | \\
        sed 's/\\bAI generated\\?\\b/Auto-generated/gi' | \\
        sed 's/Generated with Claude Code/Auto-generated/gi' | \\
        sed 's/\\bAI\\b/automated/gi' | \\
        sed 's/claude-builder/code generator/gi' \\
        > "$TEMP_FILE"
elif [ "{policy_value}" = "minimal" ]; then
    # Remove Claude mentions but keep general AI terms
    echo "$commit_msg" | \\
        sed 's/\\bClaude\\b/AI assistant/gi' | \\
        sed 's/Generated with Claude Code/Auto-generated/gi' | \\
        sed 's/claude-builder/code generator/gi' \\
        > "$TEMP_FILE"
else
    # Policy is 'allowed' - no filtering
    cp "$COMMIT_FILE" "$TEMP_FILE"
fi

# Replace original commit message
mv "$TEMP_FILE" "$COMMIT_FILE"

exit 0
"""

    def _generate_chained_commit_msg_hook(
        self, claude_mention_policy: Any, backup_hook_path: str
    ) -> str:
        """Generate chained commit-msg hook script that calls existing hook."""
        base_hook = self._generate_commit_msg_hook(claude_mention_policy)
        return f"""{base_hook.rstrip()}

# Chain with existing hook
if [ -f "{backup_hook_path}" ] && [ -x "{backup_hook_path}" ]; then
    "{backup_hook_path}" "$1"
fi

exit 0
"""

    def _generate_pre_commit_hook(self, claude_mention_policy: Any) -> str:
        """Generate pre-commit hook script for additional filtering."""
        policy_value = claude_mention_policy.value

        return f"""#!/bin/sh
# Claude Builder pre-commit hook
# Policy: {policy_value}
# Additional Claude mention filtering for staged files

# This hook could be extended to filter Claude mentions in code comments
# For now, it's a placeholder that allows commits to proceed
exit 0
"""

    def _generate_chained_pre_commit_hook(
        self, claude_mention_policy: Any, backup_hook_path: str
    ) -> str:
        """Generate chained pre-commit hook script that calls existing hook."""
        base_hook = self._generate_pre_commit_hook(claude_mention_policy)
        return f"""{base_hook.rstrip()}

# Chain with existing hook
if [ -f "{backup_hook_path}" ] && [ -x "{backup_hook_path}" ]; then
    "{backup_hook_path}"
fi

exit 0
"""
