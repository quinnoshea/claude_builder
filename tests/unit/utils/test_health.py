"""Tests for health check system."""

import json

from unittest.mock import Mock, patch

import pytest

from claude_builder.utils.health import (
    ApplicationHealthCheck,
    ConfigurationHealthCheck,
    DependencyHealthCheck,
    HealthCheck,
    HealthCheckManager,
    HealthCheckResult,
    HealthCheckType,
    HealthMonitor,
    HealthStatus,
    PerformanceHealthCheck,
    SecurityHealthCheck,
    SystemHealth,
)


class TestHealthStatus:
    """Test HealthStatus enum."""

    def test_health_status_values(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.WARNING.value == "warning"
        assert HealthStatus.CRITICAL.value == "critical"
        assert HealthStatus.UNKNOWN.value == "unknown"


class TestHealthCheckType:
    """Test HealthCheckType enum."""

    def test_health_check_type_values(self):
        """Test HealthCheckType enum values."""
        assert HealthCheckType.APPLICATION.value == "application"
        assert HealthCheckType.DEPENDENCY.value == "dependency"
        assert HealthCheckType.SECURITY.value == "security"
        assert HealthCheckType.PERFORMANCE.value == "performance"
        assert HealthCheckType.CONFIGURATION.value == "configuration"


class TestHealthCheckResult:
    """Test HealthCheckResult dataclass."""

    def test_health_check_result_creation(self):
        """Test creating HealthCheckResult."""
        result = HealthCheckResult(
            name="Test Check",
            check_type=HealthCheckType.APPLICATION,
            status=HealthStatus.HEALTHY,
            message="All systems operational",
            details={"version": "1.0"},
            duration_ms=150.5,
        )

        assert result.name == "Test Check"
        assert result.check_type == HealthCheckType.APPLICATION
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "All systems operational"
        assert result.details["version"] == "1.0"
        assert result.duration_ms == 150.5
        assert result.timestamp is not None

    def test_health_check_result_defaults(self):
        """Test HealthCheckResult with defaults."""
        result = HealthCheckResult(
            name="Simple Check",
            check_type=HealthCheckType.DEPENDENCY,
            status=HealthStatus.WARNING,
            message="Minor issues detected",
        )

        assert result.details == {}
        assert result.duration_ms == 0.0
        assert result.metadata == {}


class TestSystemHealth:
    """Test SystemHealth dataclass."""

    def test_system_health_creation(self):
        """Test creating SystemHealth."""
        results = [
            HealthCheckResult(
                name="Check 1",
                check_type=HealthCheckType.APPLICATION,
                status=HealthStatus.HEALTHY,
                message="OK",
            ),
            HealthCheckResult(
                name="Check 2",
                check_type=HealthCheckType.SECURITY,
                status=HealthStatus.WARNING,
                message="Minor issue",
            ),
        ]

        summary = {"total_checks": 2, "healthy": 1, "warnings": 1, "critical": 0}

        health = SystemHealth(
            overall_status=HealthStatus.WARNING,
            check_results=results,
            summary=summary,
            total_checks=2,
            healthy_checks=1,
            warning_checks=1,
            critical_checks=0,
            total_duration_ms=250.0,
        )

        assert health.overall_status == HealthStatus.WARNING
        assert len(health.check_results) == 2
        assert health.summary["total_checks"] == 2
        assert health.healthy_checks == 1
        assert health.warning_checks == 1


class MockHealthCheck(HealthCheck):
    """Mock health check for testing."""

    def __init__(self, name: str, status: HealthStatus, message: str = "Test message"):
        super().__init__(name, HealthCheckType.APPLICATION)
        self.mock_status = status
        self.mock_message = message

    def check(self) -> HealthCheckResult:
        """Return mock health check result."""
        return self._create_result(
            self.mock_status, self.mock_message, {"test": True}, 100.0
        )


class TestHealthCheck:
    """Test HealthCheck abstract base class."""

    def test_health_check_initialization(self):
        """Test HealthCheck initialization."""
        check = MockHealthCheck("Test Check", HealthStatus.HEALTHY)

        assert check.name == "Test Check"
        assert check.check_type == HealthCheckType.APPLICATION
        assert check.timeout == 30

    def test_create_result_method(self):
        """Test _create_result helper method."""
        check = MockHealthCheck("Test Check", HealthStatus.HEALTHY)

        result = check._create_result(
            HealthStatus.CRITICAL, "Test failed", {"error": "Test error"}, 200.5
        )

        assert result.name == "Test Check"
        assert result.check_type == HealthCheckType.APPLICATION
        assert result.status == HealthStatus.CRITICAL
        assert result.message == "Test failed"
        assert result.details["error"] == "Test error"
        assert result.duration_ms == 200.5

    def test_mock_check_execution(self):
        """Test mock health check execution."""
        check = MockHealthCheck("Test Check", HealthStatus.WARNING, "Test warning")
        result = check.check()

        assert result.status == HealthStatus.WARNING
        assert result.message == "Test warning"
        assert result.details["test"] is True
        assert result.duration_ms == 100.0


class TestApplicationHealthCheck:
    """Test ApplicationHealthCheck implementation."""

    def test_application_health_check_initialization(self):
        """Test ApplicationHealthCheck initialization."""
        check = ApplicationHealthCheck()

        assert check.name == "Application Core"
        assert check.check_type == HealthCheckType.APPLICATION

    @patch("sys.version_info", (3, 9, 7))
    @patch("claude_builder.core.analyzer.ProjectAnalyzer")
    @patch("claude_builder.core.generator.DocumentGenerator")
    @patch("claude_builder.core.config.ConfigManager")
    def test_application_health_check_healthy(
        self, mock_config, mock_generator, mock_analyzer
    ):
        """Test healthy application check."""
        # Mock successful module imports and basic functionality
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance
        mock_config_instance.create_default_config.return_value = Mock()

        check = ApplicationHealthCheck()
        result = check.check()

        assert result.status == HealthStatus.HEALTHY
        assert result.check_type == HealthCheckType.APPLICATION
        assert "operational" in result.message.lower()
        assert "python_version" in result.details
        assert "core_modules_loaded" in result.details
        assert result.details["core_modules_loaded"] is True

    @patch("sys.version_info", (3, 7, 9))  # Below minimum version
    def test_application_health_check_old_python(self):
        """Test application check with old Python version."""
        check = ApplicationHealthCheck()
        result = check.check()

        assert result.status == HealthStatus.CRITICAL
        assert "Python version 3.7 is not supported" in result.message
        assert result.details["python_version"] == "3.7.9"

    @patch("sys.version_info", (3, 9, 7))
    @patch(
        "claude_builder.core.analyzer.ProjectAnalyzer",
        side_effect=ImportError("Module not found"),
    )
    def test_application_health_check_import_error(self):
        """Test application check with import errors."""
        check = ApplicationHealthCheck()
        result = check.check()

        assert result.status == HealthStatus.CRITICAL
        assert "Failed to import core modules" in result.message
        assert "import_error" in result.details


class TestDependencyHealthCheck:
    """Test DependencyHealthCheck implementation."""

    def test_dependency_health_check_initialization(self):
        """Test DependencyHealthCheck initialization."""
        check = DependencyHealthCheck()

        assert check.name == "Dependencies"
        assert check.check_type == HealthCheckType.DEPENDENCY

    @patch("shutil.which")
    @patch("subprocess.run")
    @patch("builtins.__import__")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.unlink")
    def test_dependency_health_check_healthy(
        self, mock_unlink, mock_write, mock_import, mock_subprocess, mock_which
    ):
        """Test healthy dependency check."""
        # Mock Git availability
        mock_which.return_value = "/usr/bin/git"

        # Mock Git version check
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.34.1"
        mock_subprocess.return_value = mock_result

        # Mock successful package imports
        mock_import.return_value = Mock()

        # Mock filesystem write test
        mock_write.return_value = None
        mock_unlink.return_value = None

        check = DependencyHealthCheck()
        result = check.check()

        assert result.status == HealthStatus.HEALTHY
        assert "operational" in result.message.lower()
        assert result.details["git"]["available"] is True
        assert result.details["filesystem"]["write_access"] is True

    @patch("shutil.which", return_value=None)  # Git not found
    @patch("builtins.__import__", side_effect=ImportError("Module not found"))
    def test_dependency_health_check_missing_deps(self, mock_import, mock_which):
        """Test dependency check with missing dependencies."""
        check = DependencyHealthCheck()
        result = check.check()

        assert result.status == HealthStatus.CRITICAL
        assert "issues detected" in result.message.lower()
        assert result.details["git"]["available"] is False

    @patch("shutil.which")
    @patch("builtins.__import__")
    @patch("pathlib.Path.write_text", side_effect=PermissionError("Permission denied"))
    def test_dependency_health_check_filesystem_error(
        self, mock_write, mock_import, mock_which
    ):
        """Test dependency check with filesystem errors."""
        mock_which.return_value = "/usr/bin/git"
        mock_import.return_value = Mock()

        check = DependencyHealthCheck()
        result = check.check()

        assert result.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]
        assert result.details["filesystem"]["write_access"] is False


class TestSecurityHealthCheck:
    """Test SecurityHealthCheck implementation."""

    def test_security_health_check_initialization(self):
        """Test SecurityHealthCheck initialization."""
        check = SecurityHealthCheck()

        assert check.name == "Security Framework"
        assert check.check_type == HealthCheckType.SECURITY

    @patch("claude_builder.utils.security.SecurityValidator")
    @patch("claude_builder.utils.secure_storage.SecureTokenStorage")
    def test_security_health_check_healthy(self, mock_storage, mock_validator):
        """Test healthy security check."""
        # Mock SecurityValidator
        mock_validator_instance = Mock()
        mock_validator.return_value = mock_validator_instance
        mock_validator_instance.validate_file_path.return_value = True
        mock_validator_instance.validate_url.return_value = True

        # Mock SecureTokenStorage
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance

        check = SecurityHealthCheck()
        result = check.check()

        assert result.status == HealthStatus.HEALTHY
        assert "operational" in result.message.lower()
        assert result.details["security_validator"]["operational"] is True
        assert result.details["secure_storage"]["operational"] is True

    @patch(
        "claude_builder.utils.security.SecurityValidator",
        side_effect=Exception("Security module failed"),
    )
    def test_security_health_check_validator_error(self, mock_validator):
        """Test security check with validator errors."""
        check = SecurityHealthCheck()
        result = check.check()

        assert result.status == HealthStatus.CRITICAL
        assert "Security framework issues" in result.message
        assert result.details["security_validator"]["operational"] is False


class TestPerformanceHealthCheck:
    """Test PerformanceHealthCheck implementation."""

    def test_performance_health_check_initialization(self):
        """Test PerformanceHealthCheck initialization."""
        check = PerformanceHealthCheck()

        assert check.name == "Performance"
        assert check.check_type == HealthCheckType.PERFORMANCE

    @patch("psutil.virtual_memory")
    @patch("psutil.cpu_percent")
    @patch("psutil.disk_usage")
    @patch("psutil.Process")
    def test_performance_health_check_healthy(
        self, mock_process, mock_disk, mock_cpu, mock_memory
    ):
        """Test healthy performance check."""
        # Mock memory info (70% usage - healthy)
        mock_memory_info = Mock()
        mock_memory_info.percent = 70.0
        mock_memory_info.available = 2 * 1024 * 1024 * 1024  # 2GB available
        mock_memory_info.total = 8 * 1024 * 1024 * 1024  # 8GB total
        mock_memory.return_value = mock_memory_info

        # Mock CPU usage (60% - healthy)
        mock_cpu.return_value = 60.0

        # Mock disk usage (70% - healthy)
        mock_disk_info = Mock()
        mock_disk_info.used = 70 * 1024 * 1024 * 1024  # 70GB used
        mock_disk_info.total = 100 * 1024 * 1024 * 1024  # 100GB total
        mock_disk_info.free = 30 * 1024 * 1024 * 1024  # 30GB free
        mock_disk.return_value = mock_disk_info

        # Mock process info
        mock_process_instance = Mock()
        mock_process.return_value = mock_process_instance

        mock_memory_info_process = Mock()
        mock_memory_info_process.rss = 100 * 1024 * 1024  # 100MB
        mock_process_instance.memory_info.return_value = mock_memory_info_process
        mock_process_instance.cpu_percent.return_value = 5.0
        mock_process_instance.num_threads.return_value = 10

        check = PerformanceHealthCheck()
        result = check.check()

        assert result.status == HealthStatus.HEALTHY
        assert "normal ranges" in result.message.lower()
        assert result.details["memory"]["usage_percent"] == 70.0
        assert result.details["cpu"]["usage_percent"] == 60.0
        assert result.details["disk"]["usage_percent"] == 70.0

    @patch("psutil.virtual_memory")
    @patch("psutil.cpu_percent")
    @patch("psutil.disk_usage")
    @patch("psutil.Process")
    def test_performance_health_check_high_usage(
        self, mock_process, mock_disk, mock_cpu, mock_memory
    ):
        """Test performance check with high resource usage."""
        # Mock high memory usage (95% - critical)
        mock_memory_info = Mock()
        mock_memory_info.percent = 95.0
        mock_memory_info.available = 0.5 * 1024 * 1024 * 1024  # 0.5GB available
        mock_memory_info.total = 8 * 1024 * 1024 * 1024  # 8GB total
        mock_memory.return_value = mock_memory_info

        # Mock high CPU usage (95% - critical)
        mock_cpu.return_value = 95.0

        # Mock critical disk usage (97% - critical)
        mock_disk_info = Mock()
        mock_disk_info.used = 97 * 1024 * 1024 * 1024  # 97GB used
        mock_disk_info.total = 100 * 1024 * 1024 * 1024  # 100GB total
        mock_disk_info.free = 3 * 1024 * 1024 * 1024  # 3GB free
        mock_disk.return_value = mock_disk_info

        # Mock process info
        mock_process_instance = Mock()
        mock_process.return_value = mock_process_instance

        mock_memory_info_process = Mock()
        mock_memory_info_process.rss = 100 * 1024 * 1024  # 100MB
        mock_process_instance.memory_info.return_value = mock_memory_info_process
        mock_process_instance.cpu_percent.return_value = 5.0
        mock_process_instance.num_threads.return_value = 10

        check = PerformanceHealthCheck()
        result = check.check()

        assert result.status == HealthStatus.CRITICAL
        assert "Performance issues detected" in result.message


class TestConfigurationHealthCheck:
    """Test ConfigurationHealthCheck implementation."""

    def test_configuration_health_check_initialization(self):
        """Test ConfigurationHealthCheck initialization."""
        check = ConfigurationHealthCheck()

        assert check.name == "Configuration"
        assert check.check_type == HealthCheckType.CONFIGURATION

    @patch("claude_builder.core.config.ConfigManager")
    @patch("claude_builder.core.template_manager.TemplateManager")
    @patch("claude_builder.core.agents.UniversalAgentSystem")
    def test_configuration_health_check_healthy(
        self, mock_agent_system, mock_template_manager, mock_config_manager
    ):
        """Test healthy configuration check."""
        # Mock ConfigManager
        mock_config_instance = Mock()
        mock_config_manager.return_value = mock_config_instance
        mock_config_instance.create_default_config.return_value = Mock()
        mock_config_instance._validate_config.return_value = None

        # Mock TemplateManager
        mock_template_instance = Mock()
        mock_template_manager.return_value = mock_template_instance
        mock_template_instance.list_available_templates.return_value = [
            Mock(),
            Mock(),
        ]  # 2 templates

        # Mock UniversalAgentSystem
        mock_agent_instance = Mock()
        mock_agent_system.return_value = mock_agent_instance

        check = ConfigurationHealthCheck()
        result = check.check()

        assert result.status == HealthStatus.HEALTHY
        assert "operational" in result.message.lower()
        assert result.details["config_manager"]["operational"] is True
        assert result.details["template_system"]["operational"] is True
        assert result.details["agent_system"]["operational"] is True

    @patch(
        "claude_builder.core.config.ConfigManager",
        side_effect=Exception("Config failed"),
    )
    def test_configuration_health_check_config_error(self, mock_config_manager):
        """Test configuration check with config manager errors."""
        check = ConfigurationHealthCheck()
        result = check.check()

        assert result.status == HealthStatus.CRITICAL
        assert "Configuration issues detected" in result.message
        assert result.details["config_manager"]["operational"] is False


class TestHealthCheckManager:
    """Test HealthCheckManager functionality."""

    def test_health_check_manager_initialization(self):
        """Test HealthCheckManager initialization."""
        manager = HealthCheckManager(timeout=30)

        assert manager.timeout == 30
        assert len(manager.checks) == 5  # Default checks

        check_names = [check.name for check in manager.checks]
        assert "Application Core" in check_names
        assert "Dependencies" in check_names
        assert "Security Framework" in check_names
        assert "Performance" in check_names
        assert "Configuration" in check_names

    def test_add_check(self):
        """Test adding custom health check."""
        manager = HealthCheckManager()
        custom_check = MockHealthCheck("Custom Check", HealthStatus.HEALTHY)

        initial_count = len(manager.checks)
        manager.add_check(custom_check)

        assert len(manager.checks) == initial_count + 1
        assert custom_check in manager.checks

    def test_remove_check(self):
        """Test removing health check."""
        manager = HealthCheckManager()
        initial_count = len(manager.checks)

        result = manager.remove_check("Application Core")

        assert result is True
        assert len(manager.checks) == initial_count - 1

        check_names = [check.name for check in manager.checks]
        assert "Application Core" not in check_names

    def test_remove_nonexistent_check(self):
        """Test removing non-existent health check."""
        manager = HealthCheckManager()
        initial_count = len(manager.checks)

        result = manager.remove_check("Non-existent Check")

        assert result is False
        assert len(manager.checks) == initial_count

    def test_run_check_by_name(self):
        """Test running specific health check by name."""
        manager = HealthCheckManager()

        # Add a mock check we can control
        mock_check = MockHealthCheck("Test Check", HealthStatus.WARNING, "Test warning")
        manager.add_check(mock_check)

        result = manager.run_check_by_name("Test Check")

        assert result is not None
        assert result.name == "Test Check"
        assert result.status == HealthStatus.WARNING
        assert result.message == "Test warning"

    def test_run_check_by_name_not_found(self):
        """Test running non-existent health check by name."""
        manager = HealthCheckManager()

        result = manager.run_check_by_name("Non-existent Check")

        assert result is None

    def test_run_checks_by_type(self):
        """Test running health checks by type."""
        manager = HealthCheckManager()

        # Add mock checks of specific type
        mock_check1 = MockHealthCheck("Test Check 1", HealthStatus.HEALTHY)
        mock_check2 = MockHealthCheck("Test Check 2", HealthStatus.WARNING)
        manager.add_check(mock_check1)
        manager.add_check(mock_check2)

        results = manager.run_checks_by_type(HealthCheckType.APPLICATION)

        # Should include original Application check plus our 2 mock checks
        assert len(results) >= 3

        # All results should be APPLICATION type
        for result in results:
            assert result.check_type == HealthCheckType.APPLICATION

    def test_get_health_report(self):
        """Test getting health report as dictionary."""
        manager = HealthCheckManager()

        # Replace default checks with predictable mock checks
        manager.checks = [
            MockHealthCheck("Healthy Check", HealthStatus.HEALTHY, "All good"),
            MockHealthCheck("Warning Check", HealthStatus.WARNING, "Minor issue"),
        ]

        report = manager.get_health_report()

        assert isinstance(report, dict)
        assert "timestamp" in report
        assert "overall_status" in report
        assert "summary" in report
        assert "checks" in report

        assert len(report["checks"]) == 2
        assert report["summary"]["total_checks"] == 2
        assert report["summary"]["healthy"] == 1
        assert report["summary"]["warnings"] == 1

    def test_export_health_report(self, tmp_path):
        """Test exporting health report to file."""
        manager = HealthCheckManager()

        # Replace with simple mock checks
        manager.checks = [MockHealthCheck("Test Check", HealthStatus.HEALTHY, "OK")]

        output_file = tmp_path / "health_report.json"
        manager.export_health_report(output_file, format="json")

        assert output_file.exists()

        with output_file.open() as f:
            report_data = json.load(f)

        assert "timestamp" in report_data
        assert "overall_status" in report_data
        assert len(report_data["checks"]) == 1

    def test_export_health_report_unsupported_format(self, tmp_path):
        """Test exporting health report with unsupported format."""
        manager = HealthCheckManager()
        output_file = tmp_path / "report.xml"

        with pytest.raises(ValueError, match="Unsupported export format"):
            manager.export_health_report(output_file, format="xml")


class TestHealthMonitor:
    """Test HealthMonitor functionality."""

    def test_health_monitor_initialization(self):
        """Test HealthMonitor initialization."""
        monitor = HealthMonitor(check_interval=30, alert_threshold=5)

        assert monitor.check_interval == 30
        assert monitor.alert_threshold == 5
        assert monitor.is_monitoring is False
        assert monitor.failure_count == 0
        assert isinstance(monitor.manager, HealthCheckManager)

    def test_stop_monitoring(self):
        """Test stopping health monitoring."""
        monitor = HealthMonitor()
        monitor.is_monitoring = True

        monitor.stop_monitoring()

        assert monitor.is_monitoring is False

    @patch("time.sleep")
    @patch("builtins.print")
    def test_start_monitoring_with_failures(self, mock_print, mock_sleep):
        """Test health monitoring with consecutive failures."""
        monitor = HealthMonitor(check_interval=1, alert_threshold=2)

        # Mock the health manager to return failing health
        mock_health = Mock()
        mock_health.overall_status = HealthStatus.CRITICAL
        mock_health.critical_checks = 2
        mock_health.warning_checks = 0
        mock_health.check_results = []

        monitor.manager.run_all_checks = Mock(return_value=mock_health)

        # Mock sleep to control the loop
        def side_effect(duration):
            if mock_sleep.call_count >= 3:  # After 3 sleep calls, stop monitoring
                monitor.stop_monitoring()

        mock_sleep.side_effect = side_effect

        monitor.start_monitoring()

        # Verify monitoring was attempted
        assert mock_print.called
        assert monitor.manager.run_all_checks.called

    @patch("time.sleep", side_effect=KeyboardInterrupt())
    @patch("builtins.print")
    def test_start_monitoring_keyboard_interrupt(self, mock_print, mock_sleep):
        """Test health monitoring interrupted by keyboard."""
        monitor = HealthMonitor()

        monitor.start_monitoring()

        assert monitor.is_monitoring is False
        mock_print.assert_called_with("\nHealth monitoring stopped by user")
