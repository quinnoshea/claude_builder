"""Tests for health check CLI commands."""

from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from claude_builder.cli.health_commands import health
from claude_builder.utils.health import HealthCheckType, HealthStatus


class TestHealthCommands:
    """Test health CLI commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_health_group(self):
        """Test health command group."""
        result = self.runner.invoke(health, ["--help"])

        assert result.exit_code == 0
        assert "Health check and monitoring commands" in result.output
        assert "check" in result.output
        assert "status" in result.output
        assert "monitor" in result.output
        assert "report" in result.output

    @patch("claude_builder.cli.health_commands.HealthCheckManager")
    def test_check_command_all_healthy(self, mock_manager_class):
        """Test health check command with all checks healthy."""
        # Mock HealthCheckManager
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        # Mock healthy system health
        mock_health = Mock()
        mock_health.overall_status = HealthStatus.HEALTHY
        mock_health.total_checks = 5
        mock_health.healthy_checks = 5
        mock_health.warning_checks = 0
        mock_health.critical_checks = 0
        mock_health.total_duration_ms = 500.0
        mock_health.check_results = [
            Mock(
                name="Test Check",
                check_type=HealthCheckType.APPLICATION,
                status=HealthStatus.HEALTHY,
                message="All systems operational",
                duration_ms=100.0,
            )
        ]

        mock_manager.run_all_checks.return_value = mock_health

        result = self.runner.invoke(health, ["check"])

        assert result.exit_code == 0
        mock_manager_class.assert_called_once_with(timeout=60)
        mock_manager.run_all_checks.assert_called_once()

    @patch("claude_builder.cli.health_commands.HealthCheckManager")
    def test_check_command_with_warnings(self, mock_manager_class):
        """Test health check command with warnings."""
        # Mock HealthCheckManager
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        # Mock system health with warnings
        mock_health = Mock()
        mock_health.overall_status = HealthStatus.WARNING
        mock_health.total_checks = 5
        mock_health.healthy_checks = 3
        mock_health.warning_checks = 2
        mock_health.critical_checks = 0
        mock_health.total_duration_ms = 750.0
        mock_health.check_results = [
            Mock(
                name="Warning Check",
                check_type=HealthCheckType.PERFORMANCE,
                status=HealthStatus.WARNING,
                message="High memory usage detected",
                duration_ms=150.0,
            )
        ]

        mock_manager.run_all_checks.return_value = mock_health

        result = self.runner.invoke(health, ["check"])

        assert result.exit_code == 2  # Warning exit code
        mock_manager.run_all_checks.assert_called_once()

    @patch("claude_builder.cli.health_commands.HealthCheckManager")
    def test_check_command_with_critical_errors(self, mock_manager_class):
        """Test health check command with critical errors."""
        # Mock HealthCheckManager
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        # Mock system health with critical issues
        mock_health = Mock()
        mock_health.overall_status = HealthStatus.CRITICAL
        mock_health.total_checks = 5
        mock_health.healthy_checks = 2
        mock_health.warning_checks = 1
        mock_health.critical_checks = 2
        mock_health.total_duration_ms = 1000.0
        mock_health.check_results = [
            Mock(
                name="Critical Check",
                check_type=HealthCheckType.SECURITY,
                status=HealthStatus.CRITICAL,
                message="Security validation failed",
                duration_ms=200.0,
            )
        ]

        mock_manager.run_all_checks.return_value = mock_health

        result = self.runner.invoke(health, ["check"])

        assert result.exit_code == 1  # Critical exit code
        mock_manager.run_all_checks.assert_called_once()

    @patch("claude_builder.cli.health_commands.HealthCheckManager")
    def test_check_command_specific_type(self, mock_manager_class):
        """Test health check command with specific type."""
        # Mock HealthCheckManager
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        # Mock specific type health results
        mock_results = [
            Mock(
                name="Security Check",
                check_type=HealthCheckType.SECURITY,
                status=HealthStatus.HEALTHY,
                message="Security framework operational",
                duration_ms=120.0,
            )
        ]
        mock_manager.run_checks_by_type.return_value = mock_results

        result = self.runner.invoke(health, ["check", "--type", "security"])

        assert result.exit_code == 0
        mock_manager.run_checks_by_type.assert_called_once_with(
            HealthCheckType.SECURITY
        )

    @patch("claude_builder.cli.health_commands.HealthCheckManager")
    def test_check_command_quiet(self, mock_manager_class):
        """Test health check command in quiet mode."""
        # Mock HealthCheckManager
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        # Mock healthy system health
        mock_health = Mock()
        mock_health.overall_status = HealthStatus.HEALTHY
        mock_health.check_results = []

        mock_manager.run_all_checks.return_value = mock_health

        result = self.runner.invoke(health, ["check", "--quiet"])

        assert result.exit_code == 0
        assert result.output.strip() == "HEALTHY"  # Only status in quiet mode

    @patch("claude_builder.cli.health_commands.HealthCheckManager")
    def test_check_command_verbose(self, mock_manager_class):
        """Test health check command in verbose mode."""
        # Mock HealthCheckManager
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        # Mock system health
        mock_health = Mock()
        mock_health.overall_status = HealthStatus.HEALTHY
        mock_health.total_checks = 1
        mock_health.healthy_checks = 1
        mock_health.warning_checks = 0
        mock_health.critical_checks = 0
        mock_health.total_duration_ms = 500.0
        mock_health.check_results = [
            Mock(
                name="Test Check",
                check_type=HealthCheckType.APPLICATION,
                status=HealthStatus.HEALTHY,
                message="All systems operational",
                duration_ms=100.0,
            )
        ]

        mock_manager.run_all_checks.return_value = mock_health

        result = self.runner.invoke(health, ["check", "--verbose"])

        assert result.exit_code == 0
        assert "Duration" in result.output  # Verbose shows duration

    @patch("claude_builder.cli.health_commands.HealthCheckManager")
    def test_check_command_timeout(self, mock_manager_class):
        """Test health check command with custom timeout."""
        # Mock HealthCheckManager
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        # Mock healthy system health
        mock_health = Mock()
        mock_health.overall_status = HealthStatus.HEALTHY
        mock_health.check_results = []

        mock_manager.run_all_checks.return_value = mock_health

        result = self.runner.invoke(health, ["check", "--timeout", "120"])

        assert result.exit_code == 0
        mock_manager_class.assert_called_once_with(timeout=120)

    @patch("claude_builder.cli.health_commands.HealthCheckManager")
    def test_status_command_table_format(self, mock_manager_class):
        """Test status command with table format."""
        # Mock HealthCheckManager
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        # Mock system health
        mock_health = Mock()
        mock_health.check_results = [
            Mock(
                name="Test Check",
                status=HealthStatus.HEALTHY,
                timestamp=Mock(strftime=Mock(return_value="12:34:56")),
            )
        ]

        mock_manager.run_all_checks.return_value = mock_health

        result = self.runner.invoke(health, ["status"])

        assert result.exit_code == 0
        assert "System Health Status" in result.output
        mock_manager.run_all_checks.assert_called_once()

    @patch("claude_builder.cli.health_commands.HealthCheckManager")
    def test_status_command_json_format(self, mock_manager_class):
        """Test status command with JSON format."""
        # Mock HealthCheckManager
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        # Mock health report
        mock_report = {
            "timestamp": "2024-01-01T12:00:00",
            "overall_status": "healthy",
            "summary": {"total_checks": 1, "healthy": 1},
            "checks": [],
        }
        mock_manager.get_health_report.return_value = mock_report

        result = self.runner.invoke(health, ["status", "--format", "json"])

        assert result.exit_code == 0
        mock_manager.get_health_report.assert_called_once()

    @patch("claude_builder.cli.health_commands.HealthMonitor")
    @patch("builtins.input", side_effect=KeyboardInterrupt())  # Simulate Ctrl+C
    def test_monitor_command_keyboard_interrupt(self, mock_input, mock_monitor_class):
        """Test monitor command with keyboard interrupt."""
        # Mock HealthMonitor
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        mock_monitor.start_monitoring.side_effect = KeyboardInterrupt()

        result = self.runner.invoke(health, ["monitor", "--interval", "30"])

        assert result.exit_code == 0
        mock_monitor_class.assert_called_once_with(check_interval=30, alert_threshold=3)
        mock_monitor.start_monitoring.assert_called_once()

    @patch("claude_builder.cli.health_commands.HealthMonitor")
    def test_monitor_command_with_custom_settings(self, mock_monitor_class):
        """Test monitor command with custom settings."""
        # Mock HealthMonitor
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        mock_monitor.start_monitoring.side_effect = KeyboardInterrupt()

        result = self.runner.invoke(
            health, ["monitor", "--interval", "45", "--alert-threshold", "5"]
        )

        assert result.exit_code == 0
        mock_monitor_class.assert_called_once_with(check_interval=45, alert_threshold=5)

    def test_report_command_default_output(self, tmp_path):
        """Test report command with default output."""
        with patch(
            "claude_builder.cli.health_commands.HealthCheckManager"
        ) as mock_manager_class:
            # Mock HealthCheckManager
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            # Mock system health
            mock_health = Mock()
            mock_health.overall_status = HealthStatus.HEALTHY
            mock_health.total_checks = 1
            mock_health.healthy_checks = 1
            mock_health.warning_checks = 0
            mock_health.critical_checks = 0

            mock_manager.run_all_checks.return_value = mock_health
            mock_manager.get_health_report.return_value = {"test": "data"}
            mock_manager.export_health_report.return_value = None

            # Change to temp directory
            with self.runner.isolated_filesystem(temp_dir=tmp_path):
                result = self.runner.invoke(health, ["report"])

                assert result.exit_code == 0
                assert "Health report generated" in result.output
                mock_manager.export_health_report.assert_called_once()

    def test_report_command_custom_output(self, tmp_path):
        """Test report command with custom output file."""
        with patch(
            "claude_builder.cli.health_commands.HealthCheckManager"
        ) as mock_manager_class:
            # Mock HealthCheckManager
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            # Mock system health
            mock_health = Mock()
            mock_health.overall_status = HealthStatus.HEALTHY
            mock_health.total_checks = 1

            mock_manager.run_all_checks.return_value = mock_health
            mock_manager.get_health_report.return_value = {"test": "data"}
            mock_manager.export_health_report.return_value = None

            # Change to temp directory
            with self.runner.isolated_filesystem(temp_dir=tmp_path):
                custom_output = "custom-report.json"
                result = self.runner.invoke(
                    health, ["report", "--output", custom_output]
                )

                assert result.exit_code == 0
                assert custom_output in result.output

    def test_report_command_verbose(self, tmp_path):
        """Test report command with verbose option."""
        with patch(
            "claude_builder.cli.health_commands.HealthCheckManager"
        ) as mock_manager_class:
            with patch(
                "claude_builder.cli.health_commands._get_system_info"
            ) as mock_system_info:
                with patch(
                    "claude_builder.cli.health_commands._get_environment_info"
                ) as mock_env_info:
                    # Mock HealthCheckManager
                    mock_manager = Mock()
                    mock_manager_class.return_value = mock_manager

                    # Mock system health
                    mock_health = Mock()
                    mock_health.overall_status = HealthStatus.HEALTHY
                    mock_health.total_checks = 1

                    mock_manager.run_all_checks.return_value = mock_health
                    mock_manager.get_health_report.return_value = {"test": "data"}
                    mock_manager.export_health_report.return_value = None

                    # Mock verbose info functions
                    mock_system_info.return_value = {"platform": "Linux"}
                    mock_env_info.return_value = {"user": "testuser"}

                    # Change to temp directory
                    with self.runner.isolated_filesystem(temp_dir=tmp_path):
                        result = self.runner.invoke(health, ["report", "--verbose"])

                        assert result.exit_code == 0
                        mock_system_info.assert_called_once()
                        mock_env_info.assert_called_once()

    @patch("claude_builder.cli.health_commands.HealthCheckManager")
    def test_check_command_exception_handling(self, mock_manager_class):
        """Test health check command exception handling."""
        # Mock HealthCheckManager to raise exception
        mock_manager_class.side_effect = Exception("Test error")

        result = self.runner.invoke(health, ["check"])

        assert result.exit_code == 1
        assert "Health check failed" in result.output

    @patch("claude_builder.cli.health_commands.HealthCheckManager")
    def test_status_command_exception_handling(self, mock_manager_class):
        """Test status command exception handling."""
        # Mock HealthCheckManager to raise exception
        mock_manager_class.side_effect = Exception("Test error")

        result = self.runner.invoke(health, ["status"])

        assert result.exit_code == 1
        assert "Status check failed" in result.output

    @patch("claude_builder.cli.health_commands.HealthMonitor")
    def test_monitor_command_exception_handling(self, mock_monitor_class):
        """Test monitor command exception handling."""
        # Mock HealthMonitor to raise exception
        mock_monitor_class.side_effect = Exception("Test error")

        result = self.runner.invoke(health, ["monitor"])

        assert result.exit_code == 1
        assert "Monitoring failed" in result.output

    def test_report_command_exception_handling(self, tmp_path):
        """Test report command exception handling."""
        with patch(
            "claude_builder.cli.health_commands.HealthCheckManager"
        ) as mock_manager_class:
            # Mock HealthCheckManager to raise exception
            mock_manager_class.side_effect = Exception("Test error")

            with self.runner.isolated_filesystem(temp_dir=tmp_path):
                result = self.runner.invoke(health, ["report"])

                assert result.exit_code == 1
                assert "Report generation failed" in result.output


class TestHealthCommandHelpers:
    """Test helper functions for health commands."""

    @patch("platform.platform")
    @patch("sys.version")
    @patch("platform.architecture")
    @patch("platform.processor")
    @patch("platform.node")
    def test_get_system_info(
        self, mock_node, mock_processor, mock_arch, mock_version, mock_platform
    ):
        """Test _get_system_info helper function."""
        # Mock platform info
        mock_platform.return_value = "Linux-5.4.0"
        mock_arch.return_value = ("64bit", "ELF")
        mock_processor.return_value = "x86_64"
        mock_node.return_value = "testhost"

        from claude_builder.cli.health_commands import _get_system_info

        system_info = _get_system_info()

        assert isinstance(system_info, dict)
        assert "platform" in system_info
        assert "python_version" in system_info
        assert "architecture" in system_info
        assert "processor" in system_info
        assert "hostname" in system_info

    @patch.dict(
        "os.environ",
        {
            "USER": "testuser",
            "SHELL": "/bin/bash",
            "TERM": "xterm-256color",
            "PATH": "/usr/bin:/bin:/usr/local/bin",
        },
    )
    @patch("pathlib.Path.cwd")
    def test_get_environment_info(self, mock_cwd):
        """Test _get_environment_info helper function."""
        mock_cwd.return_value = Path("/test/directory")

        from claude_builder.cli.health_commands import _get_environment_info

        env_info = _get_environment_info()

        assert isinstance(env_info, dict)
        assert env_info["cwd"] == "/test/directory"
        assert env_info["user"] == "testuser"
        assert env_info["shell"] == "/bin/bash"
        assert env_info["term"] == "xterm-256color"
        assert isinstance(env_info["path"], list)
        assert "/usr/bin" in env_info["path"]
