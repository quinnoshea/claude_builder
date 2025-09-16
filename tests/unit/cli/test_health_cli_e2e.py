"""CLI E2E tests for health command exit codes using the registry helper.

These tests exercise the Click command end-to-end while swapping the
HealthCheckRegistry to deterministic stub checks, avoiding real system calls.
"""

from __future__ import annotations

from click.testing import CliRunner

from claude_builder.cli.health_commands import health
from claude_builder.utils.health import HealthCheckType, HealthStatus
from tests.helpers.health_registry import StubCheck, temp_health_registry


def test_health_cli_e2e_healthy_exit_zero() -> None:
    runner = CliRunner()
    with temp_health_registry(
        [
            StubCheck(
                "stub-healthy", HealthStatus.HEALTHY, HealthCheckType.APPLICATION
            ),
        ]
    ):
        result = runner.invoke(health, ["check", "--quiet"])  # minimal output
        assert result.exit_code == 0, result.output


def test_health_cli_e2e_warning_exit_two() -> None:
    runner = CliRunner()
    with temp_health_registry(
        [
            StubCheck(
                "stub-warning", HealthStatus.WARNING, HealthCheckType.APPLICATION
            ),
        ]
    ):
        result = runner.invoke(health, ["check", "--quiet"])  # minimal output
        assert result.exit_code == 2, result.output


def test_health_cli_e2e_critical_exit_one() -> None:
    runner = CliRunner()
    with temp_health_registry(
        [
            StubCheck(
                "stub-critical", HealthStatus.CRITICAL, HealthCheckType.APPLICATION
            ),
        ]
    ):
        result = runner.invoke(health, ["check", "--quiet"])  # minimal output
        assert result.exit_code == 1, result.output
