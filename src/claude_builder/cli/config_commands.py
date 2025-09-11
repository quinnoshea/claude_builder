"""Configuration management CLI commands for Claude Builder."""

from __future__ import annotations

import json

from pathlib import Path
from typing import Any

import click

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from claude_builder.core.analyzer import ProjectAnalyzer
from claude_builder.core.config import Config, ConfigManager
from claude_builder.core.models import GitIntegrationMode
from claude_builder.utils.exceptions import ConfigError


FAILED_TO_CREATE_CONFIGURATION = "Failed to create configuration"
CONFIGURATION_VALIDATION_FAILED = "Configuration validation failed"
FAILED_TO_VALIDATE_CONFIGURATION = "Failed to validate configuration"
FAILED_TO_SHOW_CONFIGURATION = "Failed to show configuration"
FAILED_TO_MIGRATE_CONFIGURATION = "Failed to migrate configuration"
FAILED_TO_CREATE_PROFILE = "Failed to create profile"
FAILED_TO_LIST_PROFILES = "Failed to list profiles"
FAILED_TO_SHOW_PROFILE = "Failed to show profile"
FAILED_TO_SET_CONFIGURATION_VALUE = "Failed to set configuration value"
FAILED_TO_RESET_CONFIGURATION = "Failed to reset configuration"
DESCRIPTION_MAX_LENGTH = 50

console = Console()


def _raise_validation_error_strict() -> None:
    """Raise validation error in strict mode."""
    error_msg = f"{CONFIGURATION_VALIDATION_FAILED} (strict mode)"
    raise click.ClickException(error_msg)


@click.group()
def config() -> None:
    """Manage claude-builder configurations."""


@config.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    required=False,
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "toml"]),
    default="json",
    help="Configuration file format",
)
@click.option("--interactive", is_flag=True, help="Interactive configuration creation")
@click.option(
    "--from-analysis", is_flag=True, help="Generate config based on project analysis"
)
def init(
    project_path: str, output_format: str, *, interactive: bool, from_analysis: bool
) -> None:
    """Create initial configuration file for a project."""
    try:
        project_path_obj = Path(project_path).resolve()
        config_manager = ConfigManager()

        # Start with default config
        config = config_manager.create_default_config(project_path_obj)

        # Enhance with project analysis if requested
        if from_analysis:
            console.print(
                "[cyan]Analyzing project to generate optimal configuration...[/cyan]"
            )
            analyzer = ProjectAnalyzer()
            analysis = analyzer.analyze(project_path_obj)

            # Customize config based on analysis
            config = _customize_config_from_analysis(config, analysis)
            console.print(
                f"[green]✓ Configuration optimized for {analysis.language} "
                f"{analysis.project_type.value}[/green]"
            )

        # Interactive configuration
        if interactive:
            config = _interactive_config_setup(config)

        # Save configuration
        config_filename = f"claude-builder.{output_format}"
        config_path = project_path_obj / config_filename

        if config_path.exists() and not Confirm.ask(
            f"Configuration file {config_filename} already exists. Overwrite?"
        ):
            console.print("[yellow]Configuration creation cancelled[/yellow]")
            return

        config_manager.save_config(config, config_path)
        console.print(f"[green]✓ Configuration saved to {config_path}[/green]")

        # Show next steps
        console.print(
            Panel(
                f"Configuration created successfully!\n\n"
                f"**Next steps:**\n"
                f"• Review and customize the configuration: `{config_filename}`\n"
                f"• Run claude-builder to use the new configuration\n"
                f"• Use `claude-builder config validate` to check configuration\n"
                f"• Create project profiles with "
                f"`claude-builder config create-profile`",
                title="Configuration Setup Complete",
            )
        )

    except Exception as e:
        console.print(f"[red]Error creating configuration: {e}[/red]")
        error_msg = f"{FAILED_TO_CREATE_CONFIGURATION}: {e}"
        raise click.ClickException(error_msg) from e


@config.command()
@click.argument("config_file", type=click.Path(exists=True), required=True)
@click.option("--strict", is_flag=True, help="Treat warnings as errors")
@click.option(
    "--project-path",
    type=click.Path(exists=True, file_okay=False),
    help="Validate against specific project",
)
def validate(config_file: str, *, strict: bool, project_path: str | None) -> None:
    """Validate a configuration file."""
    try:
        config_manager = ConfigManager()
        config_path = Path(config_file)

        console.print(f"[cyan]Validating configuration: {config_path}[/cyan]")

        # Load and validate configuration
        if project_path:
            project_path_obj = Path(project_path).resolve()
            config = config_manager.load_config(project_path_obj, config_path)

            # Additional validation with project context
            analyzer = ProjectAnalyzer()
            analysis = analyzer.analyze(project_path_obj)
            warnings = config_manager.validate_config_compatibility(config, analysis)
        else:
            # Load without project context (use low-level path for test compatibility)
            config_data = config_manager._load_config_file(config_path)  # noqa: SLF001
            config = config_manager._dict_to_config(config_data)  # noqa: SLF001
            warnings = []

        # Display results
        console.print("[green]✓ Configuration is valid[/green]")

        if warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in warnings:
                console.print(f"  • {warning}")

            if strict:
                _raise_validation_error_strict()

        if not warnings:
            console.print("[green]No issues found[/green]")

    except ConfigError as e:
        console.print(f"[red]✗ Configuration validation failed: {e}[/red]")
        raise click.ClickException(CONFIGURATION_VALIDATION_FAILED) from e
    except Exception as e:
        console.print(f"[red]Error validating configuration: {e}[/red]")
        error_msg = f"{FAILED_TO_VALIDATE_CONFIGURATION}: {e}"
        raise click.ClickException(error_msg) from e


@config.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    required=False,
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
@click.option("--section", help="Show only specific configuration section")
def show(project_path: str, output_format: str, section: str | None) -> None:
    """Show effective configuration for a project."""
    try:
        project_path_obj = Path(project_path).resolve()
        config_manager = ConfigManager()

        config = config_manager.load_config(project_path_obj)

        if output_format == "json":
            config_dict = config_manager._config_to_dict(config)  # noqa: SLF001
            if section and section in config_dict:
                config_dict = {section: config_dict[section]}
            console.print(json.dumps(config_dict, indent=2, default=str))
        elif output_format == "yaml":
            # Would need PyYAML for this
            console.print("[yellow]YAML output not yet implemented[/yellow]")
        else:
            _display_config_table(config, section)

    except Exception as e:
        console.print(f"[red]Error showing configuration: {e}[/red]")
        error_msg = f"{FAILED_TO_SHOW_CONFIGURATION}: {e}"
        raise click.ClickException(error_msg) from e


@config.command()
@click.argument("old_config", type=click.Path(exists=True), required=True)
@click.option("--output", type=click.Path(), help="Output path for migrated config")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "toml"]),
    default="json",
    help="Output format",
)
def migrate(old_config: str, output: str | None, output_format: str) -> None:
    """Migrate configuration from old format."""
    try:
        old_config_path = Path(old_config)

        # This would implement migration logic for older config versions
        console.print(f"[cyan]Migrating configuration from: {old_config_path}[/cyan]")

        # For now, just copy and validate
        config_manager = ConfigManager()
        config_data = config_manager._load_config_file(old_config_path)  # noqa: SLF001
        config = config_manager._dict_to_config(config_data)  # noqa: SLF001

        # Save migrated config
        if output:
            output_path = Path(output)
        else:
            output_path = (
                old_config_path.parent / f"claude-builder-migrated.{output_format}"
            )

        config_manager.save_config(config, output_path)
        console.print(f"[green]✓ Configuration migrated to: {output_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error migrating configuration: {e}[/red]")
        error_msg = f"{FAILED_TO_MIGRATE_CONFIGURATION}: {e}"
        raise click.ClickException(error_msg) from e


@config.command()
@click.argument("profile_name", required=True)
@click.option("--description", help="Profile description")
@click.option(
    "--config-file",
    type=click.Path(exists=True),
    help="Configuration file to use as base",
)
@click.option(
    "--project-path",
    type=click.Path(exists=True, file_okay=False),
    help="Create profile from project configuration",
)
def create_profile(
    profile_name: str,
    description: str | None,
    config_file: str | None,
    project_path: str | None,
) -> None:
    """Create a reusable project profile."""
    try:
        config_manager = ConfigManager()

        if config_file:
            # Create profile from config file
            config_path = Path(config_file)
            config_data = config_manager._load_config_file(config_path)  # noqa: SLF001
            config = config_manager._dict_to_config(config_data)  # noqa: SLF001
        elif project_path:
            # Create profile from project
            project_path_obj = Path(project_path).resolve()
            config = config_manager.load_config(project_path_obj)
        else:
            # Create profile from default
            config = Config()

        if not description:
            description = Prompt.ask(
                "Profile description", default=f"Profile for {profile_name}"
            )

        # Ensure description is never None
        final_description = description or f"Profile for {profile_name}"
        config_manager.create_project_profile(profile_name, config, final_description)
        console.print(f"[green]✓ Project profile '{profile_name}' created[/green]")

        # Show usage instructions
        console.print(
            Panel(
                f"Profile created successfully!\n\n"
                f"**Usage:**\n"
                f"• Apply to new projects: "
                f"`claude-builder --profile={profile_name} /path/to/project`\n"
                f"• List all profiles: `claude-builder config list-profiles`\n"
                f"• View profile details: "
                f"`claude-builder config show-profile {profile_name}`",
                title=f"Profile: {profile_name}",
            )
        )

    except Exception as e:
        console.print(f"[red]Error creating profile: {e}[/red]")
        error_msg = f"{FAILED_TO_CREATE_PROFILE}: {e}"
        raise click.ClickException(error_msg) from e


@config.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def list_profiles(output_format: str) -> None:
    """List available project profiles."""
    try:
        config_manager = ConfigManager()
        profiles = config_manager.list_project_profiles()

        if not profiles:
            console.print("[yellow]No project profiles found[/yellow]")
            return

        if output_format == "json":
            console.print(json.dumps(profiles, indent=2, default=str))
        else:
            _display_profiles_table(profiles)

    except Exception as e:
        console.print(f"[red]Error listing profiles: {e}[/red]")
        error_msg = f"{FAILED_TO_LIST_PROFILES}: {e}"
        raise click.ClickException(error_msg) from e


@config.command()
@click.argument("profile_name", required=True)
def show_profile(profile_name: str) -> None:
    """Show details of a project profile."""
    try:
        config_manager = ConfigManager()
        profiles = config_manager.list_project_profiles()

        profile = next((p for p in profiles if p["name"] == profile_name), None)
        if not profile:
            console.print(f"[red]Profile not found: {profile_name}[/red]")
            return

        # Display profile information
        info_panel = (
            f"[bold]{profile['name']}[/bold]\n\n"
            f"[bold]Description:[/bold] "
            f"{profile.get('description', 'No description')}\n"
            f"[bold]Created:[/bold] {profile.get('created', 'Unknown')}\n\n"
            f"[bold]Configuration Preview:[/bold]\n"
        )

        # Show key configuration sections
        config_preview = {}
        if "config" in profile:
            config_data = profile["config"]
            config_preview = {
                "agents": config_data.get("agents", {}).get("priority_agents", []),
                "templates": config_data.get("templates", {}).get(
                    "preferred_templates", []
                ),
                "git_integration": config_data.get("git_integration", {}).get(
                    "mode", "unknown"
                ),
            }

        info_panel += f"\n{json.dumps(config_preview, indent=2)}"

        console.print(Panel(info_panel, title=f"Profile: {profile_name}"))

    except Exception as e:
        console.print(f"[red]Error showing profile: {e}[/red]")
        error_msg = f"{FAILED_TO_SHOW_PROFILE}: {e}"
        raise click.ClickException(error_msg) from e


def _customize_config_from_analysis(config: Config, analysis: Any) -> Config:
    """Customize configuration based on project analysis."""
    # Customize based on language
    if analysis.language == "python":
        config.agents.priority_agents = [
            "python-pro",
            "backend-developer",
            "test-automator",
        ]
        config.templates.preferred_templates = [
            "python-web" if "web" in str(analysis.project_type) else "python-cli"
        ]
    elif analysis.language == "rust":
        config.agents.priority_agents = [
            "rust-engineer",
            "performance-engineer",
            "cli-developer",
        ]
        config.templates.preferred_templates = ["rust-cli"]
    elif analysis.language == "javascript":
        config.agents.priority_agents = [
            "javascript-pro",
            "frontend-developer",
            "backend-developer",
        ]
        config.templates.preferred_templates = ["javascript-react"]

    # Customize based on project type
    if "web" in str(analysis.project_type).lower():
        config.agents.priority_agents.extend(["ui-designer", "api-designer"])
    elif "cli" in str(analysis.project_type).lower():
        config.agents.priority_agents.extend(
            ["cli-developer", "documentation-engineer"]
        )

    return config


def _interactive_config_setup(config: Config) -> Config:
    """Interactive configuration setup."""
    console.print("[bold]Interactive Configuration Setup[/bold]")
    console.print("Configure key settings (press Enter to keep current values)\n")

    # Analysis settings
    console.print("[cyan]Analysis Settings[/cyan]")
    new_threshold = IntPrompt.ask(
        "Confidence threshold (0-100)", default=config.analysis.confidence_threshold
    )
    config.analysis.confidence_threshold = new_threshold

    # Git integration
    console.print("\n[cyan]Git Integration[/cyan]")
    git_modes = ["no_integration", "exclude_generated", "track_generated"]
    current_mode = config.git_integration.mode.value
    git_mode = Prompt.ask(
        "Git integration mode", choices=git_modes, default=current_mode
    )
    config.git_integration.mode = GitIntegrationMode(git_mode)

    # Claude mention policy
    mention_policies = ["forbidden", "minimal", "allowed"]
    current_policy = config.git_integration.claude_mention_policy.value
    mention_policy = Prompt.ask(
        "Claude mention policy", choices=mention_policies, default=current_policy
    )
    from claude_builder.core.models import ClaudeMentionPolicy

    config.git_integration.claude_mention_policy = ClaudeMentionPolicy(mention_policy)

    # User preferences
    console.print("\n[cyan]User Preferences[/cyan]")
    config.user_preferences.prefer_verbose_output = Confirm.ask(
        "Enable verbose output by default?",
        default=config.user_preferences.prefer_verbose_output,
    )

    return config


def _display_config_table(config: Any, section: str | None = None) -> None:
    """Display configuration in table format."""
    if section:
        # Show specific section
        section_data = getattr(config, section, None)
        if section_data:
            table = Table(title=f"Configuration: {section}")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="white")

            for key, value in section_data.__dict__.items():
                table.add_row(key, str(value))

            console.print(table)
        else:
            console.print(f"[red]Unknown section: {section}[/red]")
    else:
        # Show overview
        table = Table(title="Configuration Overview")
        table.add_column("Section", style="cyan")
        table.add_column("Key Settings", style="white")

        table.add_row(
            "Analysis",
            f"Threshold: {config.analysis.confidence_threshold}%, "
            f"Cache: {config.analysis.cache_enabled}",
        )
        table.add_row(
            "Templates",
            f"Preferred: {', '.join(config.templates.preferred_templates) or 'Auto'}",
        )
        table.add_row(
            "Agents", f"Priority: {', '.join(config.agents.priority_agents) or 'Auto'}"
        )
        table.add_row(
            "Git Integration",
            f"Mode: {config.git_integration.mode.value}, "
            f"Mentions: {config.git_integration.claude_mention_policy.value}",
        )
        table.add_row(
            "Output",
            f"Format: {config.output.format}, Backup: {config.output.backup_existing}",
        )

        console.print(table)


def _display_profiles_table(profiles: list[Any]) -> None:
    """Display project profiles in table format."""
    table = Table(title="Project Profiles")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Created", style="dim")

    for profile in profiles:
        table.add_row(
            profile["name"],
            profile.get("description", "No description")[:DESCRIPTION_MAX_LENGTH]
            + (
                "..."
                if len(profile.get("description", "")) > DESCRIPTION_MAX_LENGTH
                else ""
            ),
            profile.get("created", "Unknown")[:10],  # Show date only
        )

    console.print(table)


@config.command()
@click.argument("key", required=True)
@click.argument("value", required=True)
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    required=False,
)
def set_value(key: str, value: str, project_path: str = ".") -> None:
    """Set configuration value for project."""
    try:
        project_path_obj = Path(project_path).resolve()
        config_manager = ConfigManager()

        # Load current config
        config = config_manager.load_config(project_path_obj)

        # Set value using dot notation (e.g., "git_integration.mode")
        keys = key.split(".")
        current = config

        # Navigate to parent object
        for k in keys[:-1]:
            if hasattr(current, k):
                current = getattr(current, k)
            else:
                console.print(f"[red]Invalid configuration path: {key}[/red]")
                return

        # Set the final value
        final_key = keys[-1]
        if hasattr(current, final_key):
            # Convert string value to appropriate type
            current_value = getattr(current, final_key)
            converted_value: Any
            if isinstance(current_value, bool):
                converted_value = value.lower() in ("true", "1", "yes", "on")
            elif isinstance(current_value, int):
                converted_value = int(value)
            elif isinstance(current_value, list):
                converted_value = [v.strip() for v in value.split(",")]
            else:
                converted_value = value

            setattr(current, final_key, converted_value)

            # Save updated config
            config_path = project_path_obj / "claude-builder.json"
            config_manager.save_config(config, config_path)

            console.print(f"[green]✓ Set {key} = {converted_value}[/green]")
        else:
            console.print(f"[red]Invalid configuration key: {final_key}[/red]")

    except Exception as e:
        console.print(f"[red]Error setting configuration value: {e}[/red]")
        error_msg = f"{FAILED_TO_SET_CONFIGURATION_VALUE}: {e}"
        raise click.ClickException(error_msg) from e


@config.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    required=False,
)
@click.option("--force", is_flag=True, help="Force reset without confirmation")
def reset(project_path: str, *, force: bool) -> None:
    """Reset configuration to defaults."""
    try:
        project_path_obj = Path(project_path).resolve()
        config_manager = ConfigManager()

        if not force:
            from rich.prompt import Confirm

            if not Confirm.ask("Reset configuration to defaults?"):
                console.print("[yellow]Reset cancelled[/yellow]")
                return

        # Create default config
        config = config_manager.create_default_config(project_path_obj)

        # Save config
        config_path = project_path_obj / "claude-builder.json"
        config_manager.save_config(config, config_path)

        console.print("[green]✓ Configuration reset to defaults[/green]")

    except Exception as e:
        console.print(f"[red]Error resetting configuration: {e}[/red]")
        error_msg = f"{FAILED_TO_RESET_CONFIGURATION}: {e}"
        raise click.ClickException(error_msg) from e
