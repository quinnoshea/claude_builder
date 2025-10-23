"""Tests for health check system."""

from pathlib import Path
from unittest.mock import Mock, patch

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
)


class TestHealthStatus:
    """Test HealthStatus enum."""

    def test_health_status_values(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.WARNING.value == "warning"
        assert HealthStatus.CRITICAL.value == "critical"
        assert HealthStatus.UNKNOWN.value == "unknown"


class TestHealthCheckResult:
    """Test HealthCheckResult dataclass."""

    def test_health_check_result_fields(self):
        """Test HealthCheckResult fields."""
        result = HealthCheckResult(
            name="Test Check",
            check_type=HealthCheckType.APPLICATION,
            status=HealthStatus.HEALTHY,
            message="All good",
            details={"key": "value"},
            duration_ms=100.0,
        )

        assert result.name == "Test Check"
        assert result.check_type == HealthCheckType.APPLICATION
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "All good"
        assert result.details["key"] == "value"
        assert result.duration_ms == 100.0


class MockHealthCheck(HealthCheck):
    """Mock health check for testing."""

    def __init__(self, name: str, status: HealthStatus):
        super().__init__(name, HealthCheckType.APPLICATION)
        self._status = status

    def check(self) -> HealthCheckResult:  # type: ignore[override]
        """Return mock health check result."""
        return HealthCheckResult(
            name=self.name,
            check_type=self.check_type,
            status=self._status,
            message="Mock result",
            details={"mock": True},
            duration_ms=50.0,
        )


class TestApplicationHealthCheck:
    """Test ApplicationHealthCheck implementation."""

    def test_application_health_check_python_version(self):
        """Test that unsupported Python versions are critical."""
        from collections import namedtuple

        VersionInfo = namedtuple("version_info", ["major", "minor", "micro"])

        with patch("sys.version_info", VersionInfo(3, 7, 9)):
            check = ApplicationHealthCheck()
            result = check.check()

            assert result.status == HealthStatus.CRITICAL
            assert "Python version 3.7 is not supported" in result.message
            assert result.details["python_version"] == "3.7.9"

    @patch(
        "claude_builder.core.config.ConfigManager",
        side_effect=ImportError("Module not found"),
    )
    def test_application_health_check_import_error(self, mock_config):
        """Test application check with import errors."""
        from collections import namedtuple

        VersionInfo = namedtuple("version_info", ["major", "minor", "micro"])
        version_info_mock = VersionInfo(3, 9, 7)

        with patch("sys.version_info", version_info_mock):
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
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.unlink")
    def test_dependency_health_check_healthy(
        self, mock_unlink, mock_write, mock_subprocess, mock_which
    ):
        """Test healthy dependency check."""
        # Mock Git availability
        mock_which.return_value = "/usr/bin/git"

        # Mock Git version check
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.34.1"
        mock_subprocess.return_value = mock_result

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
    def test_dependency_health_check_missing_deps(self, mock_which):
        """Test dependency check with missing dependencies."""
        # Store the original __import__ to avoid recursion
        original_import = __import__

        def mock_import(name, *args, **kwargs):
            # Allow normal imports except for our test packages
            if name in ["click", "rich", "toml", "pathlib", "psutil"]:
                raise ImportError("Module not found")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            check = DependencyHealthCheck()
            result = check.check()

            assert result.status == HealthStatus.CRITICAL
            assert "dependency issues detected" in result.message.lower()
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

    @patch("shutil.which")
    @patch("subprocess.run")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.unlink")
    def test_dependency_health_check_devops_tools(
        self, mock_unlink, mock_write, mock_subprocess, mock_which
    ):
        """Test DevOps tools validation (terraform, kubectl, docker, helm, ansible)."""

        def which_side_effect(tool_name):
            devops_tools = ["git", "terraform", "kubectl", "docker", "helm", "ansible"]
            return f"/usr/bin/{tool_name}" if tool_name in devops_tools else None

        mock_which.side_effect = which_side_effect

        # Mock successful version checks
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "version 1.0.0"
        mock_subprocess.return_value = mock_result

        check = DependencyHealthCheck(scope="devops")
        result = check.check()

        # Verify devops tools are checked
        assert "devops_terraform" in result.details
        assert "devops_kubectl" in result.details
        assert "devops_docker" in result.details
        assert "devops_helm" in result.details
        assert "devops_ansible" in result.details

        # Verify all are available
        assert result.details["devops_terraform"]["available"] is True
        assert result.details["devops_kubectl"]["available"] is True
        assert result.details["devops_docker"]["available"] is True
        assert result.details["devops_helm"]["available"] is True
        assert result.details["devops_ansible"]["available"] is True

    @patch("shutil.which")
    @patch("subprocess.run")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.unlink")
    def test_dependency_health_check_cloud_tools(
        self, mock_unlink, mock_write, mock_subprocess, mock_which
    ):
        """Test cloud CLI tools validation (aws, gcloud, az)."""

        def which_side_effect(tool_name):
            cloud_tools = ["git", "aws", "gcloud", "az"]
            return f"/usr/bin/{tool_name}" if tool_name in cloud_tools else None

        mock_which.side_effect = which_side_effect

        # Mock successful version checks
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "version 1.0.0"
        mock_subprocess.return_value = mock_result

        check = DependencyHealthCheck(scope="cloud")
        result = check.check()

        # Verify cloud tools are checked
        assert "cloud_aws" in result.details
        assert "cloud_gcloud" in result.details
        assert "cloud_az" in result.details

        # Verify all are available
        assert result.details["cloud_aws"]["available"] is True
        assert result.details["cloud_gcloud"]["available"] is True
        assert result.details["cloud_az"]["available"] is True

    @patch("shutil.which")
    @patch("subprocess.run")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.unlink")
    def test_dependency_health_check_scope_core(
        self, mock_unlink, mock_write, mock_subprocess, mock_which
    ):
        """Test scope filtering - core scope should only check git and python packages."""
        mock_which.return_value = "/usr/bin/git"

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.34.1"
        mock_subprocess.return_value = mock_result

        check = DependencyHealthCheck(scope="core")
        result = check.check()

        # Git should be checked
        assert "git" in result.details

        # Python packages should be checked
        assert "package_click" in result.details

        # DevOps and cloud tools should NOT be checked
        assert "devops_terraform" not in result.details
        assert "cloud_aws" not in result.details

    @patch("shutil.which")
    def test_dependency_health_check_missing_devops_tools_recommendations(
        self, mock_which
    ):
        """Test that missing DevOps tools generate structured recommendations."""
        # Only git is available
        mock_which.side_effect = lambda tool: (
            "/usr/bin/git" if tool == "git" else None
        )

        check = DependencyHealthCheck(scope="devops")
        result = check.check()

        # Should have recommendations for missing tools
        assert len(result.recommendations) > 0

        # Check for at least one DevOps tool recommendation
        rec_text = "\n".join(result.recommendations)
        # At least one of these should be mentioned
        has_devops_rec = any(
            tool in rec_text.lower()
            for tool in ["terraform", "kubectl", "docker", "helm", "ansible"]
        )
        assert has_devops_rec


class TestSecurityHealthCheck:
    """Test SecurityHealthCheck implementation."""

    def test_security_health_check_initialization(self):
        """Test SecurityHealthCheck initialization."""
        check = SecurityHealthCheck()

        assert check.name == "Security Framework"
        assert check.check_type == HealthCheckType.SECURITY

    @patch("claude_builder.utils.security.SecurityValidator")
    @patch("claude_builder.utils.secure_storage.SecureTokenManager")
    @patch(
        "claude_builder.utils.secure_storage.is_secure_storage_available",
        return_value=True,
    )
    def test_security_health_check_healthy(
        self, mock_is_available, mock_storage, mock_validator
    ):
        """Test healthy security check."""
        from claude_builder.utils.exceptions import SecurityError

        # Mock SecurityValidator
        mock_validator_instance = Mock()
        mock_validator.return_value = mock_validator_instance

        # Mock file path validation to behave correctly
        def mock_validate_file_path(path):
            if path in [
                "../../../etc/passwd",
                "test\x00.txt",
                "/absolute/path/file.txt",
            ]:
                raise SecurityError("Invalid path")
            return True

        # Mock URL validation
        def mock_validate_url(url):
            if url.startswith("http://") or url.startswith("ftp://"):
                raise SecurityError("Insecure URL")
            if "localhost" in url or "malicious" in url:
                raise SecurityError("Blocked domain")
            return True

        mock_validator_instance.validate_file_path.side_effect = mock_validate_file_path
        mock_validator_instance.validate_url.side_effect = mock_validate_url
        # Content validation should raise SecurityError on malicious inputs
        mock_validator_instance.validate_file_content.side_effect = (
            lambda content, *_args, **_kwargs: (_ for _ in ()).throw(
                SecurityError("Blocked content")
            )
        )

        # Mock SecureTokenManager minimal functionality
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance
        mock_storage_instance._get_or_create_encryption_key.return_value = b"key"

        check = SecurityHealthCheck()
        result = check.check()

        assert result.status in [HealthStatus.HEALTHY, HealthStatus.WARNING]
        assert result.details["security_validator"]["operational"] is True
        assert result.details["secure_storage"]["operational"] is True


class TestPerformanceHealthCheck:
    """Test PerformanceHealthCheck implementation."""

    @patch("psutil.virtual_memory")
    @patch("psutil.cpu_percent", return_value=5.0)
    @patch("psutil.disk_usage")
    def test_performance_health_check_healthy(self, mock_disk_usage, _cpu, mock_mem):
        """Test healthy performance check."""
        mock_mem.return_value = Mock(
            percent=30.0, available=8 * 1024**3, total=16 * 1024**3
        )
        mock_disk_usage.return_value = Mock(used=100, total=1000, free=900 * 1024**3)

        check = PerformanceHealthCheck()
        result = check.check()

        assert result.status == HealthStatus.HEALTHY


class TestConfigurationHealthCheck:
    """Test ConfigurationHealthCheck implementation."""

    @patch("claude_builder.core.config.ConfigManager")
    @patch("claude_builder.core.template_manager.TemplateManager")
    @patch("claude_builder.core.agents.UniversalAgentSystem")
    def test_configuration_health_check_healthy(self, *_):
        check = ConfigurationHealthCheck()
        result = check.check()
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.WARNING]


class TestHealthCheckManager:
    """Test HealthCheckManager operations."""

    def test_default_checks_registered(self):
        manager = HealthCheckManager()
        check_names = {c.name for c in manager.checks}
        assert {
            "Application Core",
            "Dependencies",
            "Security Framework",
            "Performance",
            "Configuration",
        }.issubset(check_names)

    def test_add_check(self):
        manager = HealthCheckManager()
        custom_check = MockHealthCheck("Custom Check", HealthStatus.HEALTHY)
        initial_count = len(manager.checks)
        manager.add_check(custom_check)
        assert len(manager.checks) == initial_count + 1
        assert custom_check in manager.checks

    def test_remove_check(self):
        manager = HealthCheckManager()
        initial_count = len(manager.checks)
        result = manager.remove_check("Application Core")
        assert result is True
        assert len(manager.checks) == initial_count - 1

    def test_run_checks_by_type(self):
        manager = HealthCheckManager()
        results = manager.run_checks_by_type(HealthCheckType.APPLICATION)
        assert isinstance(results, list)
        assert all(
            r.check_type == HealthCheckType.APPLICATION
            for r in results
            if hasattr(r, "check_type")
        )

    def test_get_health_report_and_export(self, tmp_path: Path):
        manager = HealthCheckManager()
        report = manager.get_health_report()
        assert report["overall_status"] in {"healthy", "warning", "critical", "unknown"}
        out = tmp_path / "health.json"
        manager.export_health_report(out, format="json")
        assert out.exists()


class TestHealthMonitor:
    """Test HealthMonitor behavior (non-blocking aspects)."""

    @patch("time.sleep", return_value=None)
    def test_stop_condition_and_alert_threshold(self, _sleep):
        monitor = HealthMonitor(check_interval=0, alert_threshold=1)
        # Stop immediately after one iteration by monkey-patching is_monitoring
        monitor.is_monitoring = True
        # We will run a single pass of run_all_checks by setting flag then clearing
        original_run = monitor.manager.run_all_checks

        def run_once():
            monitor.is_monitoring = False
            return original_run()

        monitor.manager.run_all_checks = run_once  # type: ignore[assignment]
        monitor.start_monitoring()
