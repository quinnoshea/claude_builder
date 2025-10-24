"""Health check CLI commands for Claude Builder.

This module provides CLI commands for health monitoring, status checking,
and system diagnostics for production environments.
"""

from __future__ import annotations

import sys

from pathlib import Path
from typing import Any

import click

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from claude_builder.utils.exceptions import PerformanceError, SecurityError
from claude_builder.utils.health import (
    HealthCheckManager,
    HealthCheckType,
    HealthMonitor,
    HealthStatus,
    SystemHealth,
)


console = Console()


@click.group()
def health() -> None:
    """Health check and monitoring commands.

    Monitor the application health, dependencies, performance,
    and security framework status for production environments.

    Examples:
        claude-builder health check           # Run all health checks
        claude-builder health status          # Show status summary
        claude-builder health monitor         # Start continuous monitoring
        claude-builder health report --json   # Export detailed report
    """


@health.command()
@click.option(
    "--type",
    "check_type",
    type=click.Choice([t.value for t in HealthCheckType]),
    help="Run only specific type of health checks",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed check information")
@click.option("--quiet", "-q", is_flag=True, help="Show only overall status")
@click.option(
    "--timeout",
    type=int,
    default=60,
    help="Health check timeout in seconds (default: 60)",
)
@click.option(
    "--scope",
    type=click.Choice(["core", "devops", "cloud", "all"]),
    default="all",
    help="Scope of dependency checks: core (git+python), devops (terraform, docker, etc.), cloud (aws, gcloud, az), or all",
)
def check(
    check_type: str | None, verbose: bool, quiet: bool, timeout: int, scope: str
) -> None:
    """Run health checks and display results.

    Performs comprehensive health checks on application components,
    dependencies, security framework, and system performance.

    Examples:
        claude-builder health check                    # All checks
        claude-builder health check --type security   # Security only
        claude-builder health check --verbose          # Detailed output
        claude-builder health check --quiet            # Status only
    """
    try:
        manager = HealthCheckManager(timeout=timeout, scope=scope)

        if not quiet:
            console.print(
                Panel(
                    "[bold blue]Claude Builder Health Check[/bold blue]\n"
                    f"Running {check_type if check_type else 'all'} health checks...",
                    title="Health Monitor",
                )
            )

        health: SystemHealth | None = None
        # Run health checks with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=quiet,
        ) as progress:
            task = progress.add_task("Running health checks...", total=None)

            if check_type:
                # Run specific type of checks
                health_type = HealthCheckType(check_type)
                results = manager.run_checks_by_type(health_type)

                # Create SystemHealth object from results
                critical_count = sum(
                    1 for r in results if r.status == HealthStatus.CRITICAL
                )
                warning_count = sum(
                    1 for r in results if r.status == HealthStatus.WARNING
                )
                healthy_count = sum(
                    1 for r in results if r.status == HealthStatus.HEALTHY
                )

                if critical_count > 0:
                    overall_status = HealthStatus.CRITICAL
                elif warning_count > 0:
                    overall_status = HealthStatus.WARNING
                else:
                    overall_status = HealthStatus.HEALTHY

                total_duration = sum(getattr(r, "duration_ms", 0.0) for r in results)

                health = SystemHealth(
                    overall_status=overall_status,
                    check_results=results,
                    summary={
                        "total_checks": len(results),
                        "healthy": healthy_count,
                        "warnings": warning_count,
                        "critical": critical_count,
                        "total_duration_ms": total_duration,
                    },
                    total_checks=len(results),
                    healthy_checks=healthy_count,
                    warning_checks=warning_count,
                    critical_checks=critical_count,
                    total_duration_ms=total_duration,
                )
            else:
                # Run all checks
                health = manager.run_all_checks()

            progress.update(
                task, completed=True, description="✓ Health checks complete"
            )

        # Display results
        _display_health_results(health, verbose, quiet)

        # Exit with appropriate code (use Click Exit for predictable testing)
        if health.overall_status == HealthStatus.CRITICAL:
            raise click.exceptions.Exit(1)
        if health.overall_status == HealthStatus.WARNING:
            raise click.exceptions.Exit(2)
        # For HEALTHY status, return normally without raising exception
    except click.exceptions.Exit:
        # Re-raise Click Exit exceptions (don't catch our own exit codes)
        raise
    except (PerformanceError, SecurityError, OSError, RuntimeError, ValueError) as e:
        console.print(f"[red]Health check failed: {e}[/red]")
        raise click.exceptions.Exit(1)


@health.command()
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format (default: table)",
)
def status(format: str) -> None:
    """Show current system health status.

    Displays a quick overview of system health without running
    full diagnostics. Useful for monitoring dashboards.

    Examples:
        claude-builder health status           # Table format
        claude-builder health status --format json  # JSON format
    """
    try:
        manager = HealthCheckManager()
        health = manager.run_all_checks()

        if format == "json":
            report = manager.get_health_report()
            console.print_json(data=report)
        else:
            _display_status_table(health)

    except (PerformanceError, SecurityError, OSError, RuntimeError, ValueError) as e:
        console.print(f"[red]Status check failed: {e}[/red]")
        sys.exit(1)


@health.command()
@click.option(
    "--interval", type=int, default=60, help="Check interval in seconds (default: 60)"
)
@click.option(
    "--alert-threshold",
    type=int,
    default=3,
    help="Number of consecutive failures before alert (default: 3)",
)
@click.option("--output", type=click.Path(), help="Log monitoring output to file")
def monitor(interval: int, alert_threshold: int, output: str | None) -> None:
    """Start continuous health monitoring.

    Runs health checks at regular intervals and triggers alerts
    when issues are detected. Use Ctrl+C to stop monitoring.

    Examples:
        claude-builder health monitor                    # Default 60s interval
        claude-builder health monitor --interval 30     # 30s interval
        claude-builder health monitor --output health.log  # Log to file
    """
    try:
        console.print(
            Panel(
                f"[bold green]Health Monitoring Started[/bold green]\n"
                f"Interval: {interval} seconds\n"
                f"Alert threshold: {alert_threshold} failures\n"
                f"Press Ctrl+C to stop",
                title="Health Monitor",
            )
        )

        monitor = HealthMonitor(
            check_interval=interval, alert_threshold=alert_threshold
        )

        if output:
            console.print(f"Logging to: {output}")

        # Start monitoring (blocking)
        monitor.start_monitoring()

    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped by user[/yellow]")
    except (PerformanceError, SecurityError, OSError, RuntimeError, ValueError) as e:
        console.print(f"[red]Monitoring failed: {e}[/red]")
        sys.exit(1)


@health.command()
@click.option(
    "--output", type=click.Path(), help="Output file path (default: health-report.json)"
)
@click.option(
    "--format",
    type=click.Choice(["json"]),
    default="json",
    help="Report format (default: json)",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Include detailed diagnostic information"
)
def report(output: str | None, format: str, verbose: bool) -> None:
    """Generate detailed health report.

    Creates a comprehensive health report with detailed diagnostics,
    performance metrics, and system information for analysis.

    Examples:
        claude-builder health report                     # Default output
        claude-builder health report --output report.json  # Custom file
        claude-builder health report --verbose           # Detailed info
    """
    try:
        manager = HealthCheckManager()

        console.print("Generating comprehensive health report...")

        # Generate report
        health = manager.run_all_checks()
        report_data = manager.get_health_report()

        # Add verbose information if requested
        if verbose:
            report_data["system_info"] = _get_system_info()
            report_data["environment_info"] = _get_environment_info()

        # Determine output path
        output_path = Path(output) if output else Path("health-report.json")

        # Export report
        manager.export_health_report(output_path, format=format)

        console.print(f"[green]✓ Health report generated: {output_path}[/green]")

        # Show summary
        _display_report_summary(health, output_path)
    except (PerformanceError, SecurityError, OSError, RuntimeError, ValueError) as e:
        console.print(f"[red]Report generation failed: {e}[/red]")
        raise click.exceptions.Exit(1)


def _display_health_results(health: SystemHealth, verbose: bool, quiet: bool) -> None:
    """Display health check results."""
    if quiet:
        # Just show overall status
        status_color = {
            HealthStatus.HEALTHY: "green",
            HealthStatus.WARNING: "yellow",
            HealthStatus.CRITICAL: "red",
            HealthStatus.UNKNOWN: "dim",
        }
        color = status_color.get(health.overall_status, "white")
        console.print(f"[{color}]{health.overall_status.value.upper()}[/{color}]")
        return

    # Show detailed results
    table = Table(title="Health Check Results")
    table.add_column("Check", style="cyan")
    table.add_column("Type", style="blue")
    table.add_column("Status", justify="center")
    table.add_column("Message", style="white")

    if verbose:
        table.add_column("Duration", justify="right", style="dim")

    for result in health.check_results:
        status_color = {
            HealthStatus.HEALTHY: "green",
            HealthStatus.WARNING: "yellow",
            HealthStatus.CRITICAL: "red",
            HealthStatus.UNKNOWN: "dim",
        }

        color = status_color.get(result.status, "white")
        status_text = Text(result.status.value.upper(), style=color)

        message_text = str(result.message)
        if len(message_text) > 80:
            message_text = message_text[:80] + "..."

        row = [
            str(result.name),
            getattr(result.check_type, "value", str(result.check_type)),
            status_text,
            message_text,
        ]

        if verbose:
            row.append(f"{result.duration_ms:.1f}ms")

        table.add_row(*row)

        # Show recommendations under the row when verbose
        if verbose and getattr(result, "recommendations", None):
            rec_text = "\n".join(f"  • {rec}" for rec in result.recommendations)
            # Table includes Duration column when verbose, so add an empty cell to align
            table.add_row(
                "", "", "", f"[bold yellow]Recommendations:[/]\n{rec_text}", ""
            )

    console.print(table)

    # Summary panel
    summary_text = (
        f"Total: {health.total_checks} | "
        f"[green]Healthy: {health.healthy_checks}[/green] | "
        f"[yellow]Warnings: {health.warning_checks}[/yellow] | "
        f"[red]Critical: {health.critical_checks}[/red]"
    )

    if verbose:
        summary_text += f" | Duration: {health.total_duration_ms:.1f}ms"

    status_color = {
        HealthStatus.HEALTHY: "green",
        HealthStatus.WARNING: "yellow",
        HealthStatus.CRITICAL: "red",
        HealthStatus.UNKNOWN: "dim",
    }

    panel_color = status_color.get(health.overall_status, "white")

    console.print(
        Panel(
            f"[bold {panel_color}]Overall Status: {health.overall_status.value.upper()}[/bold {panel_color}]\n"
            f"{summary_text}",
            title="Summary",
        )
    )


def _display_status_table(health: SystemHealth) -> None:
    """Display status in table format."""
    table = Table(title="System Health Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Last Check", style="dim")

    for result in health.check_results:
        status_color = {
            HealthStatus.HEALTHY: "green",
            HealthStatus.WARNING: "yellow",
            HealthStatus.CRITICAL: "red",
            HealthStatus.UNKNOWN: "dim",
        }

        color = status_color.get(result.status, "white")
        status_text = Text(result.status.value.upper(), style=color)

        ts = getattr(result, "timestamp", None)
        ts_str = ts.strftime("%H:%M:%S") if ts and hasattr(ts, "strftime") else "-"
        table.add_row(str(result.name), status_text, ts_str)

    console.print(table)


def _display_report_summary(health: SystemHealth, output_path: Path) -> None:
    """Display report generation summary."""
    status_emoji = {
        HealthStatus.HEALTHY: "✅",
        HealthStatus.WARNING: "⚠️",
        HealthStatus.CRITICAL: "❌",
        HealthStatus.UNKNOWN: "❓",
    }

    emoji = status_emoji.get(health.overall_status, "")

    def _to_int(x: Any) -> int:
        try:
            return int(x)
        except (TypeError, ValueError):
            return 0

    total = _to_int(getattr(health, "total_checks", 0))
    warns = _to_int(getattr(health, "warning_checks", 0))
    crits = _to_int(getattr(health, "critical_checks", 0))

    console.print(
        Panel(
            f"{emoji} [bold]Overall Status: {health.overall_status.value.upper()}[/bold]\n"
            f"Report saved to: {output_path}\n"
            f"Checks completed: {total}\n"
            f"Issues found: {warns + crits}",
            title="Health Report Summary",
        )
    )


def _get_system_info() -> dict[str, Any]:
    """Get detailed system information."""
    import platform

    return {
        "platform": platform.platform(),
        "python_version": sys.version,
        "architecture": platform.architecture(),
        "processor": platform.processor(),
        "hostname": platform.node(),
    }


def _get_environment_info() -> dict[str, Any]:
    """Get environment information."""
    import os

    return {
        "cwd": str(Path.cwd()),
        "user": os.environ.get("USER", "unknown"),
        "shell": os.environ.get("SHELL", "unknown"),
        "term": os.environ.get("TERM", "unknown"),
        "path": os.environ.get("PATH", "").split(":"),
    }
