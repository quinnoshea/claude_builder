"""Git integration management CLI commands for Claude Builder."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from claude_builder.core.config import ConfigManager
from claude_builder.utils.exceptions import GitError
from claude_builder.utils.git import (
    GitBackupManager,
    GitHookManager,
    GitIntegrationManager,
)

FAILED_TO_CHECK_GIT_STATUS = "Failed to check git status"
EXCLUDE_SETUP_FAILED = "Exclude setup failed"
FAILED_TO_SETUP_EXCLUDES = "Failed to setup excludes"
UNEXCLUDE_OPERATION_FAILED = "Unexclude operation failed"
FAILED_TO_REMOVE_EXCLUDES = "Failed to remove excludes"
FAILED_TO_INSTALL_HOOKS = "Failed to install hooks"
HOOK_REMOVAL_FAILED = "Hook removal failed"
FAILED_TO_REMOVE_HOOKS = "Failed to remove hooks"
FAILED_TO_LIST_BACKUPS = "Failed to list backups"
ROLLBACK_FAILED = "Rollback failed"
FAILED_TO_CLEANUP_BACKUPS = "Failed to cleanup backups"
EXCLUDE_SETUP_FAILED_ERROR = "Exclude setup failed"
UNEXCLUDE_OPERATION_FAILED_ERROR = "Unexclude operation failed"
FAILED_TO_CREATE_BACKUP = "Failed to create backup"
FAILED_TO_RESTORE_BACKUP = "Failed to restore backup"

console = Console()


@click.group()
def git():
    """Manage git integration features."""


@git.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    required=False,
)
def status(project_path: str):
    """Show git integration status for a project."""
    try:
        project_path_obj = Path(project_path).resolve()

        # Check if it's a git repository
        if not (project_path_obj / ".git").exists():
            console.print("[red]Not a git repository[/red]")
            return

        console.print(f"[bold]Git Integration Status for {project_path_obj}[/bold]\n")

        # Check .git/info/exclude
        exclude_file = project_path_obj / ".git" / "info" / "exclude"
        exclude_status = "Not found"
        claude_section = False

        if exclude_file.exists():
            with open(exclude_file, encoding="utf-8") as f:
                content = f.read()
            exclude_status = f"Exists ({len(content.splitlines())} lines)"
            claude_section = "Claude Builder" in content

        # Check git hooks
        hooks_dir = project_path_obj / ".git" / "hooks"
        commit_msg_hook = hooks_dir / "commit-msg"
        pre_commit_hook = hooks_dir / "pre-commit"

        commit_msg_status = "Not installed"
        pre_commit_status = "Not installed"

        if commit_msg_hook.exists():
            with open(commit_msg_hook, encoding="utf-8") as f:
                content = f.read()
            if "Claude Builder" in content:
                commit_msg_status = "Installed (Claude Builder)"
            else:
                commit_msg_status = "Installed (Other)"

        if pre_commit_hook.exists():
            with open(pre_commit_hook, encoding="utf-8") as f:
                content = f.read()
            if "Claude Builder" in content:
                pre_commit_status = "Installed (Claude Builder)"
            else:
                pre_commit_status = "Installed (Other)"

        # Check backups
        backup_manager = GitBackupManager()
        backups = backup_manager.list_backups(project_path_obj)

        # Display status table
        table = Table(title="Git Integration Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Details", style="dim")

        table.add_row(
            ".git/info/exclude",
            "[green]✓[/green]" if exclude_file.exists() else "[red]✗[/red]",
            exclude_status,
        )
        table.add_row(
            "Claude exclude section",
            "[green]✓[/green]" if claude_section else "[red]✗[/red]",
            "Active" if claude_section else "Not found",
        )
        table.add_row(
            "commit-msg hook",
            (
                "[green]✓[/green]"
                if "Claude Builder" in commit_msg_status
                else (
                    "[yellow]○[/yellow]" if commit_msg_hook.exists() else "[red]✗[/red]"
                )
            ),
            commit_msg_status,
        )
        table.add_row(
            "pre-commit hook",
            (
                "[green]✓[/green]"
                if "Claude Builder" in pre_commit_status
                else (
                    "[yellow]○[/yellow]" if pre_commit_hook.exists() else "[red]✗[/red]"
                )
            ),
            pre_commit_status,
        )
        table.add_row(
            "Backups",
            "[green]✓[/green]" if backups else "[yellow]○[/yellow]",
            f"{len(backups)} available" if backups else "None",
        )

        console.print(table)

        # Load and display current configuration
        try:
            config_manager = ConfigManager()
            config = config_manager.load_config(project_path_obj)

            console.print("\n[bold]Current Configuration:[/bold]")
            console.print(
                f"Git integration: [cyan]{config.git_integration.enabled}[/cyan]"
            )
            console.print(f"Mode: [cyan]{config.git_integration.mode.value}[/cyan]")
            console.print(
                f"Claude mention policy: [cyan]{config.git_integration.claude_mention_policy.value}[/cyan]"
            )
            console.print(
                f"Backup before changes: [cyan]{config.git_integration.backup_before_changes}[/cyan]"
            )

        except Exception as e:
            console.print(f"\n[yellow]Could not load configuration: {e}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error checking git status: {e}[/red]")
        raise click.ClickException(f"{FAILED_TO_CHECK_GIT_STATUS}: {e}")


@git.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    required=False,
)
@click.option(
    "--force", is_flag=True, help="Force exclude setup even if already configured"
)
def exclude(project_path: str, force: bool):
    """Add generated files to .git/info/exclude."""
    try:
        project_path_obj = Path(project_path).resolve()

        if not (project_path_obj / ".git").exists():
            console.print("[red]Not a git repository[/red]")
            return

        # Load configuration to get files to exclude
        config_manager = ConfigManager()
        config = config_manager.load_config(project_path_obj)

        git_manager = GitIntegrationManager()

        # Check if already configured
        exclude_file = project_path_obj / ".git" / "info" / "exclude"
        if exclude_file.exists() and not force:
            with open(exclude_file, encoding="utf-8") as f:
                content = f.read()
            if "Claude Builder" in content:
                console.print(
                    "[yellow]Claude Builder exclude section already exists[/yellow]"
                )
                if not Confirm.ask("Reconfigure exclude patterns?"):
                    return
                force = True

        console.print("[cyan]Adding generated files to .git/info/exclude...[/cyan]")

        # Add excludes
        result = git_manager.exclude_manager.add_excludes(
            project_path_obj, config.git_integration.files_to_exclude
        )

        if result.success:
            console.print("[green]✓ Files added to .git/info/exclude[/green]")
            for operation in result.operations_performed:
                console.print(f"  {operation}")

            # Show what was excluded
            console.print("\n[bold]Excluded patterns:[/bold]")
            for pattern in config.git_integration.files_to_exclude:
                console.print(f"  • {pattern}")
        else:
            console.print("[red]Failed to add excludes:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
            raise click.ClickException(EXCLUDE_SETUP_FAILED)

    except Exception as e:
        console.print(f"[red]Error setting up excludes: {e}[/red]")
        raise click.ClickException(f"{FAILED_TO_SETUP_EXCLUDES}: {e}")


@git.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    required=False,
)
def unexclude(project_path: str):
    """Remove files from .git/info/exclude."""
    try:
        project_path_obj = Path(project_path).resolve()

        if not (project_path_obj / ".git").exists():
            console.print("[red]Not a git repository[/red]")
            return

        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config(project_path_obj)

        if not Confirm.ask(
            "Remove Claude Builder exclude patterns from .git/info/exclude?"
        ):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

        console.print("[cyan]Removing files from .git/info/exclude...[/cyan]")

        git_manager = GitIntegrationManager()
        result = git_manager.exclude_manager.remove_excludes(
            project_path_obj, config.git_integration.files_to_exclude
        )

        if result.success:
            console.print(
                "[green]✓ Claude Builder patterns removed from .git/info/exclude[/green]"
            )
            for operation in result.operations_performed:
                console.print(f"  {operation}")
        else:
            console.print("[red]Failed to remove excludes:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
            raise click.ClickException(UNEXCLUDE_OPERATION_FAILED)

    except Exception as e:
        console.print(f"[red]Error removing excludes: {e}[/red]")
        raise click.ClickException(f"{FAILED_TO_REMOVE_EXCLUDES}: {e}")


@git.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    required=False,
)
@click.option(
    "--policy",
    type=click.Choice(["forbidden", "minimal", "allowed"]),
    help="Claude mention policy for hooks",
)
@click.option("--pre-commit", is_flag=True, help="Also install pre-commit hook")
def install_hooks(project_path: str, policy: Optional[str], pre_commit: bool):
    """Install git hooks for Claude mention control."""
    try:
        project_path_obj = Path(project_path).resolve()

        if not (project_path_obj / ".git").exists():
            console.print("[red]Not a git repository[/red]")
            return

        # Load configuration to get policy
        config_manager = ConfigManager()
        config = config_manager.load_config(project_path_obj)

        # Use provided policy or config policy
        if policy:
            from claude_builder.core.models import ClaudeMentionPolicy

            claude_policy = ClaudeMentionPolicy(policy)
        else:
            claude_policy = config.git_integration.claude_mention_policy

        console.print(
            f"[cyan]Installing git hooks with policy: {claude_policy.value}[/cyan]"
        )

        hook_manager = GitHookManager()

        # Install commit-msg hook
        result = hook_manager.install_commit_msg_hook(project_path_obj, claude_policy)

        if result.success:
            console.print("[green]✓ commit-msg hook installed[/green]")
            for operation in result.operations_performed:
                console.print(f"  {operation}")
        else:
            console.print("[red]Failed to install commit-msg hook:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")

        # Install pre-commit hook if requested
        if pre_commit:
            result = hook_manager.install_pre_commit_hook(
                project_path_obj, claude_policy
            )

            if result.success:
                console.print("[green]✓ pre-commit hook installed[/green]")
                for operation in result.operations_performed:
                    console.print(f"  {operation}")
            else:
                console.print("[red]Failed to install pre-commit hook:[/red]")
                for error in result.errors:
                    console.print(f"  • {error}")

        # Show what the hooks do
        console.print(
            Panel(
                f"**Git hooks installed with policy: {claude_policy.value}**\n\n"
                f"**commit-msg hook:** Filters Claude mentions from commit messages\n"
                f"**pre-commit hook:** {'Installed' if pre_commit else 'Not installed'} - Checks staged files for Claude mentions\n\n"
                f"**Policy behavior:**\n"
                f"• forbidden: Remove all Claude/AI mentions\n"
                f"• minimal: Remove Claude-specific mentions, keep general AI terms\n"
                f"• allowed: No filtering (hooks not needed)",
                title="Git Hooks Configuration",
            )
        )

    except Exception as e:
        console.print(f"[red]Error installing hooks: {e}[/red]")
        raise click.ClickException(f"{FAILED_TO_INSTALL_HOOKS}: {e}")


@git.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    required=False,
)
@click.option("--force", is_flag=True, help="Force removal without confirmation")
def uninstall_hooks(project_path: str, force: bool):
    """Remove git hooks installed by Claude Builder."""
    try:
        project_path_obj = Path(project_path).resolve()

        if not (project_path_obj / ".git").exists():
            console.print("[red]Not a git repository[/red]")
            return

        if not force:
            if not Confirm.ask("Remove Claude Builder git hooks?"):
                console.print("[yellow]Operation cancelled[/yellow]")
                return

        console.print("[cyan]Removing git hooks...[/cyan]")

        hook_manager = GitHookManager()
        result = hook_manager.uninstall_hooks(project_path_obj)

        if result.success:
            console.print("[green]✓ Git hooks removed[/green]")
            for operation in result.operations_performed:
                console.print(f"  {operation}")
        else:
            console.print("[red]Failed to remove hooks:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
            raise click.ClickException(HOOK_REMOVAL_FAILED)

    except Exception as e:
        console.print(f"[red]Error removing hooks: {e}[/red]")
        raise click.ClickException(f"{FAILED_TO_REMOVE_HOOKS}: {e}")


@git.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    required=False,
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def list_backups(project_path: str, output_format: str):
    """List available git configuration backups."""
    try:
        project_path_obj = Path(project_path).resolve()

        if not (project_path_obj / ".git").exists():
            console.print("[red]Not a git repository[/red]")
            return

        backup_manager = GitBackupManager()
        backups = backup_manager.list_backups(project_path_obj)

        if not backups:
            console.print("[yellow]No backups found[/yellow]")
            return

        if output_format == "json":
            import json

            console.print(json.dumps(backups, indent=2, default=str))
        else:
            table = Table(title="Git Configuration Backups")
            table.add_column("Backup ID", style="cyan")
            table.add_column("Created", style="white")
            table.add_column("Files", style="dim")

            for backup in backups:
                table.add_row(
                    backup["backup_id"],
                    backup["timestamp"][:19].replace("T", " "),
                    f"{len(backup.get('backed_up_files', []))} files",
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing backups: {e}[/red]")
        raise click.ClickException(f"{FAILED_TO_LIST_BACKUPS}: {e}")


@git.command()
@click.argument("backup_id", required=True)
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    required=False,
)
@click.option("--force", is_flag=True, help="Force rollback without confirmation")
def rollback(backup_id: str, project_path: str, force: bool):
    """Rollback git configuration to a previous backup."""
    try:
        project_path_obj = Path(project_path).resolve()

        if not (project_path_obj / ".git").exists():
            console.print("[red]Not a git repository[/red]")
            return

        if not force:
            if not Confirm.ask(f"Rollback git configuration to backup '{backup_id}'?"):
                console.print("[yellow]Rollback cancelled[/yellow]")
                return

        console.print(f"[cyan]Rolling back to backup: {backup_id}[/cyan]")

        backup_manager = GitBackupManager()
        success = backup_manager.restore_backup(project_path_obj, backup_id)

        if success:
            console.print(
                f"[green]✓ Successfully rolled back to backup {backup_id}[/green]"
            )
        else:
            console.print(f"[red]Failed to rollback to backup {backup_id}[/red]")
            raise click.ClickException(ROLLBACK_FAILED)

    except GitError as e:
        console.print(f"[red]Rollback error: {e}[/red]")
        raise click.ClickException(f"{ROLLBACK_FAILED}: {e}")
    except Exception as e:
        console.print(f"[red]Error during rollback: {e}[/red]")
        raise click.ClickException(f"{ROLLBACK_FAILED}: {e}")


@git.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    required=False,
)
@click.option("--keep", type=int, default=5, help="Number of backups to keep")
@click.option("--force", is_flag=True, help="Force cleanup without confirmation")
def cleanup_backups(project_path: str, keep: int, force: bool):
    """Clean up old git configuration backups."""
    try:
        project_path_obj = Path(project_path).resolve()

        if not (project_path_obj / ".git").exists():
            console.print("[red]Not a git repository[/red]")
            return

        backup_manager = GitBackupManager()
        backups = backup_manager.list_backups(project_path_obj)

        if len(backups) <= keep:
            console.print(
                f"[green]Only {len(backups)} backups found, nothing to clean up[/green]"
            )
            return

        to_remove = len(backups) - keep

        if not force:
            if not Confirm.ask(
                f"Remove {to_remove} old backups (keeping {keep} most recent)?"
            ):
                console.print("[yellow]Cleanup cancelled[/yellow]")
                return

        console.print(
            f"[cyan]Cleaning up old backups (keeping {keep} most recent)...[/cyan]"
        )

        removed_count = backup_manager.cleanup_old_backups(project_path_obj, keep)

        console.print(f"[green]✓ Removed {removed_count} old backups[/green]")

    except Exception as e:
        console.print(f"[red]Error cleaning up backups: {e}[/red]")
        raise click.ClickException(f"{FAILED_TO_CLEANUP_BACKUPS}: {e}")


def setup_exclude(project_path: str):
    """Setup git exclude patterns."""
    try:
        project_path_obj = Path(project_path).resolve()

        if not (project_path_obj / ".git").exists():
            console.print("[red]Not a git repository[/red]")
            return

        # Load configuration to get files to exclude
        config_manager = ConfigManager()
        config = config_manager.load_config(project_path_obj)

        git_manager = GitIntegrationManager()

        console.print("[cyan]Adding generated files to .git/info/exclude...[/cyan]")

        # Add excludes
        result = git_manager.exclude_manager.add_excludes(
            project_path_obj, config.git_integration.files_to_exclude
        )

        if result.success:
            console.print("[green]✓ Files added to .git/info/exclude[/green]")
            for operation in result.operations_performed:
                console.print(f"  {operation}")

            # Show what was excluded
            console.print("\n[bold]Excluded patterns:[/bold]")
            for pattern in config.git_integration.files_to_exclude:
                console.print(f"  • {pattern}")
        else:
            console.print("[red]Failed to add excludes:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
            raise GitError(EXCLUDE_SETUP_FAILED_ERROR)

    except Exception as e:
        console.print(f"[red]Error setting up excludes: {e}[/red]")
        raise GitError(f"{FAILED_TO_SETUP_EXCLUDES}: {e}")


def remove_exclude(project_path: str):
    """Remove git exclude patterns."""
    try:
        project_path_obj = Path(project_path).resolve()

        if not (project_path_obj / ".git").exists():
            console.print("[red]Not a git repository[/red]")
            return

        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config(project_path_obj)

        console.print("[cyan]Removing files from .git/info/exclude...[/cyan]")

        git_manager = GitIntegrationManager()
        result = git_manager.exclude_manager.remove_excludes(
            project_path_obj, config.git_integration.files_to_exclude
        )

        if result.success:
            console.print(
                "[green]✓ Claude Builder patterns removed from .git/info/exclude[/green]"
            )
            for operation in result.operations_performed:
                console.print(f"  {operation}")
        else:
            console.print("[red]Failed to remove excludes:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
            raise GitError(UNEXCLUDE_OPERATION_FAILED_ERROR)

    except Exception as e:
        console.print(f"[red]Error removing excludes: {e}[/red]")
        raise GitError(f"{FAILED_TO_REMOVE_EXCLUDES}: {e}")


def backup(project_path: str = "."):
    """Create backup of git configuration."""
    try:
        project_path_obj = Path(project_path).resolve()

        if not (project_path_obj / ".git").exists():
            console.print("[red]Not a git repository[/red]")
            return None

        backup_manager = GitBackupManager()
        backup_id = backup_manager.create_backup(project_path_obj)

        console.print(f"[green]✓ Backup created: {backup_id}[/green]")
        return backup_id

    except Exception as e:
        console.print(f"[red]Error creating backup: {e}[/red]")
        raise GitError(f"{FAILED_TO_CREATE_BACKUP}: {e}")


def restore(backup_id: str, project_path: str = "."):
    """Restore git configuration from backup."""
    try:
        project_path_obj = Path(project_path).resolve()

        if not (project_path_obj / ".git").exists():
            console.print("[red]Not a git repository[/red]")
            return

        backup_manager = GitBackupManager()
        success = backup_manager.restore_backup(project_path_obj, backup_id)

        if success:
            console.print(f"[green]✓ Restored from backup: {backup_id}[/green]")
        else:
            console.print(f"[red]Failed to restore backup: {backup_id}[/red]")
            raise GitError(f"{FAILED_TO_RESTORE_BACKUP}: {backup_id}")

    except Exception as e:
        console.print(f"[red]Error restoring backup: {e}[/red]")
        raise GitError(f"{FAILED_TO_RESTORE_BACKUP}: {e}")
