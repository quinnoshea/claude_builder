"""Health check system for Claude Builder production monitoring.

This module provides a comprehensive health check framework for monitoring
the application's health, dependencies, and performance in production environments.
"""

from __future__ import annotations

import json
import platform
import shutil
import sys
import time

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

from claude_builder.utils.exceptions import SecurityError


class HealthStatus(Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class HealthCheckType(Enum):
    """Types of health checks available."""

    APPLICATION = "application"
    DEPENDENCY = "dependency"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CONFIGURATION = "configuration"


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""

    name: str
    check_type: HealthCheckType
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """Overall system health report."""

    overall_status: HealthStatus
    check_results: List[HealthCheckResult]
    summary: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    total_checks: int = 0
    healthy_checks: int = 0
    warning_checks: int = 0
    critical_checks: int = 0
    total_duration_ms: float = 0.0


class HealthCheck(ABC):
    """Abstract base class for health checks."""

    def __init__(self, name: str, check_type: HealthCheckType, timeout: int = 30):
        self.name = name
        self.check_type = check_type
        self.timeout = timeout

    @abstractmethod
    def check(self) -> HealthCheckResult:
        """Perform the health check and return result."""

    def _create_result(
        self,
        status: HealthStatus,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
    ) -> HealthCheckResult:
        """Create a standardized health check result."""
        return HealthCheckResult(
            name=self.name,
            check_type=self.check_type,
            status=status,
            message=message,
            details=details or {},
            duration_ms=duration_ms,
        )


class ApplicationHealthCheck(HealthCheck):
    """Health check for core application functionality."""

    def __init__(self) -> None:
        super().__init__("Application Core", HealthCheckType.APPLICATION)

    def check(self) -> HealthCheckResult:
        """Check core application health."""
        start_time = time.time()

        try:
            # Check Python environment
            python_version = sys.version_info
            if python_version < (3, 8):
                return self._create_result(
                    HealthStatus.CRITICAL,
                    f"Python version {python_version.major}.{python_version.minor} is not supported (minimum 3.8)",
                    {
                        "python_version": f"{python_version.major}.{python_version.minor}.{python_version.micro}"
                    },
                )

            # Check core modules can be imported
            try:
                from claude_builder.core.config import ConfigManager

                # Test basic functionality
                config_manager = ConfigManager()
                _ = config_manager.create_default_config(Path.cwd())

                details = {
                    "python_version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                    "platform": platform.platform(),
                    "core_modules_loaded": True,
                    "config_system": "operational",
                }

                duration_ms = (time.time() - start_time) * 1000
                return self._create_result(
                    HealthStatus.HEALTHY,
                    "Application core systems are operational",
                    details,
                    duration_ms,
                )

            except ImportError as e:
                return self._create_result(
                    HealthStatus.CRITICAL,
                    f"Failed to import core modules: {e}",
                    {"import_error": str(e)},
                )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return self._create_result(
                HealthStatus.CRITICAL,
                f"Application health check failed: {e}",
                {"error": str(e)},
                duration_ms,
            )


class DependencyHealthCheck(HealthCheck):
    """Health check for external dependencies."""

    def __init__(self) -> None:
        super().__init__("Dependencies", HealthCheckType.DEPENDENCY)

    def check(self) -> HealthCheckResult:
        """Check external dependencies health."""
        start_time = time.time()

        try:
            issues = []
            details: Dict[str, Any] = {}

            # Check Git availability
            git_path = shutil.which("git")
            if git_path:
                details["git"] = {"available": True, "path": git_path}

                # Check Git version
                try:
                    import subprocess

                    result = subprocess.run(
                        ["git", "--version"],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        details["git"]["version"] = result.stdout.strip()
                    else:
                        issues.append("Git version check failed")
                except (subprocess.TimeoutExpired, OSError) as e:
                    issues.append(f"Git version check error: {e}")
            else:
                issues.append("Git not found in PATH")
                details["git"] = {"available": False}

            # Check required Python packages
            required_packages = ["click", "rich", "toml", "pathlib", "psutil"]

            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package)
                    details[f"package_{package}"] = {"available": True}
                except ImportError:
                    missing_packages.append(package)
                    details[f"package_{package}"] = {"available": False}

            if missing_packages:
                issues.append(f"Missing Python packages: {', '.join(missing_packages)}")

            # Check filesystem permissions
            try:
                test_file = Path.cwd() / ".claude-builder-health-test"
                test_file.write_text("test")
                test_file.unlink()
                details["filesystem"] = {"write_access": True}
            except (OSError, PermissionError) as e:
                issues.append(f"Filesystem write access failed: {e}")
                details["filesystem"] = {"write_access": False, "error": str(e)}

            duration_ms = (time.time() - start_time) * 1000

            if not issues:
                return self._create_result(
                    HealthStatus.HEALTHY,
                    "All dependencies are available and operational",
                    details,
                    duration_ms,
                )
            status = (
                HealthStatus.CRITICAL
                if missing_packages or "Git not found" in str(issues)
                else HealthStatus.WARNING
            )
            return self._create_result(
                status,
                f"Dependency issues detected: {'; '.join(issues)}",
                details,
                duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return self._create_result(
                HealthStatus.CRITICAL,
                f"Dependency health check failed: {e}",
                {"error": str(e)},
                duration_ms,
            )


class SecurityHealthCheck(HealthCheck):
    """Health check for security framework."""

    def __init__(self) -> None:
        super().__init__("Security Framework", HealthCheckType.SECURITY)

    def check(self) -> HealthCheckResult:
        """Check security framework health."""
        start_time = time.time()

        try:
            details: Dict[str, Any] = {}
            issues = []

            # Test SecurityValidator functionality
            try:
                from claude_builder.utils.security import SecurityValidator

                validator = SecurityValidator()

                # Test file path validation with various scenarios
                test_cases = [
                    ("valid/test/path.txt", True, "valid_relative_path"),
                    ("../../../etc/passwd", False, "path_traversal_attack"),
                    ("test\x00.txt", False, "null_byte_injection"),
                    ("/absolute/path/file.txt", False, "absolute_path_rejection"),
                ]

                path_validation_results: Dict[str, Dict[str, Any]] = {}
                for test_path_str, expected_valid, test_name in test_cases:
                    try:
                        # Pass string directly to validate_file_path
                        result = validator.validate_file_path(test_path_str)
                        path_validation_results[test_name] = {
                            "expected": expected_valid,
                            "actual": result,
                            "passed": result == expected_valid,
                        }
                    except SecurityError:
                        path_validation_results[test_name] = {
                            "expected": expected_valid,
                            "actual": False,
                            "passed": not expected_valid,  # Expecting SecurityError for invalid paths
                        }
                    except Exception as e:
                        path_validation_results[test_name] = {
                            "expected": expected_valid,
                            "actual": False,
                            "passed": False,
                            "error": str(e),
                        }

                details["file_path_validation"] = {
                    "operational": True,
                    "test_results": path_validation_results,
                }

                # Test URL validation with safe and unsafe URLs
                url_test_cases = [
                    ("https://github.com/user/repo", True, "github_url"),
                    (
                        "https://raw.githubusercontent.com/user/repo/main/file.txt",
                        True,
                        "github_raw_url",
                    ),
                    ("http://localhost:8080/api", False, "localhost_url"),
                    ("https://malicious-site.com/data", False, "unknown_domain"),
                    ("ftp://example.com/file", False, "non_https_protocol"),
                ]

                url_validation_results: Dict[str, Dict[str, Any]] = {}
                for test_url, expected_valid, test_name in url_test_cases:
                    try:
                        validator.validate_url(test_url)
                        url_validation_results[test_name] = {
                            "expected": expected_valid,
                            "actual": True,
                            "passed": expected_valid,
                        }
                    except SecurityError:
                        url_validation_results[test_name] = {
                            "expected": expected_valid,
                            "actual": False,
                            "passed": not expected_valid,  # Expecting SecurityError for invalid URLs
                        }
                    except Exception as e:
                        url_validation_results[test_name] = {
                            "expected": expected_valid,
                            "actual": False,
                            "passed": False,
                            "error": str(e),
                        }

                details["url_validation"] = {
                    "operational": True,
                    "test_results": url_validation_results,
                }

                # Test content validation and sanitization (focus on implemented patterns)
                malicious_content_tests = [
                    ("<script>alert('xss')</script>", "xss_script"),
                    ("javascript:alert(1)", "javascript_protocol"),
                    ("eval(malicious_code)", "eval_injection"),
                    ("import os; os.system('rm -rf /')", "python_system_call"),
                ]

                sanitization_results: Dict[str, Dict[str, Any]] = {}
                for test_content, test_name in malicious_content_tests:
                    try:
                        # Use validate_file_content method - it throws exceptions for dangerous content
                        sanitized = validator.validate_file_content(
                            test_content, f"test_{test_name}.txt"
                        )
                        # If we get here, the content was not detected as dangerous (unexpected)
                        sanitization_results[test_name] = {
                            "original_length": len(test_content),
                            "sanitized_length": len(sanitized),
                            "was_modified": test_content != sanitized,
                            "passed": False,  # Should have thrown exception for malicious content
                            "error": "Dangerous content was not detected",
                        }
                    except SecurityError as e:
                        # This is expected for malicious content - SecurityValidator throws exceptions
                        sanitization_results[test_name] = {
                            "expected_exception": True,
                            "exception_message": str(e),
                            "passed": True,  # Successfully detected dangerous content
                        }
                    except Exception as e:
                        sanitization_results[test_name] = {
                            "error": str(e),
                            "passed": False,
                        }

                details["content_sanitization"] = {
                    "operational": True,
                    "test_results": sanitization_results,
                }

                details["security_validator"] = {"operational": True}

                # Check for any failed validation tests
                failed_tests = []
                for validation_type, validation_data in details.items():
                    if (
                        isinstance(validation_data, dict)
                        and "test_results" in validation_data
                    ):
                        test_results = validation_data["test_results"]
                        if isinstance(test_results, dict):
                            for test_name, test_result in test_results.items():
                                if isinstance(
                                    test_result, dict
                                ) and not test_result.get("passed", True):
                                    failed_tests.append(
                                        f"{validation_type}.{test_name}"
                                    )

                if failed_tests:
                    issues.append(
                        f"Security validation tests failed: {', '.join(failed_tests)}"
                    )

            except Exception as e:
                issues.append(f"SecurityValidator failed: {e}")
                details["security_validator"] = {"operational": False, "error": str(e)}

            # Check secure storage functionality
            try:
                from claude_builder.utils.secure_storage import (
                    SecureTokenManager,
                    is_secure_storage_available,
                )

                # Test secure storage availability and initialization
                storage_available = is_secure_storage_available()

                # Test token manager initialization (without actually storing)
                try:
                    storage = SecureTokenManager()

                    # Test encryption key functionality (without storing)
                    encryption_key = storage._get_or_create_encryption_key()

                    details["secure_storage"] = {
                        "operational": True,
                        "crypto_available": storage_available,
                        "encryption_key_available": encryption_key is not None,
                        "methods_available": {
                            "store_token": hasattr(storage, "store_token"),
                            "get_token": hasattr(storage, "get_token"),
                            "delete_token": hasattr(storage, "delete_token"),
                        },
                    }

                except Exception as storage_error:
                    # If SecureTokenManager fails, fall back to checking fallback storage
                    try:
                        from claude_builder.utils.secure_storage import (
                            FallbackSecureStorage,
                        )

                        fallback_storage = FallbackSecureStorage()

                        details["secure_storage"] = {
                            "operational": True,
                            "crypto_available": False,
                            "fallback_storage": True,
                            "fallback_methods": {
                                "store_token": hasattr(fallback_storage, "store_token"),
                                "get_token": hasattr(fallback_storage, "get_token"),
                                "delete_token": hasattr(
                                    fallback_storage, "delete_token"
                                ),
                            },
                        }
                    except Exception as fallback_error:
                        issues.append(
                            f"Both secure storage and fallback failed: {storage_error}, {fallback_error}"
                        )
                        details["secure_storage"] = {
                            "operational": False,
                            "error": f"Storage: {storage_error}, Fallback: {fallback_error}",
                        }

            except Exception as e:
                issues.append(f"Secure storage failed: {e}")
                details["secure_storage"] = {"operational": False, "error": str(e)}

            duration_ms = (time.time() - start_time) * 1000

            if not issues:
                return self._create_result(
                    HealthStatus.HEALTHY,
                    "Security framework is operational with all validations passing",
                    details,
                    duration_ms,
                )
            return self._create_result(
                HealthStatus.CRITICAL,
                f"Security framework issues: {'; '.join(issues)}",
                details,
                duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return self._create_result(
                HealthStatus.CRITICAL,
                f"Security health check failed: {e}",
                {"error": str(e)},
                duration_ms,
            )


class PerformanceHealthCheck(HealthCheck):
    """Health check for system performance metrics."""

    def __init__(self) -> None:
        super().__init__("Performance", HealthCheckType.PERFORMANCE)

    def check(self) -> HealthCheckResult:
        """Check system performance health."""
        start_time = time.time()

        try:
            issues = []
            details: Dict[str, Any] = {}

            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)

            details["memory"] = {
                "usage_percent": memory_usage_percent,
                "available_mb": round(memory_available_mb, 2),
                "total_mb": round(memory.total / (1024 * 1024), 2),
            }

            if memory_usage_percent > 90:
                issues.append(f"High memory usage: {memory_usage_percent:.1f}%")
            elif memory_usage_percent > 80:
                issues.append(f"Warning: Memory usage at {memory_usage_percent:.1f}%")

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            details["cpu"] = {"usage_percent": cpu_percent, "count": psutil.cpu_count()}

            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_usage_percent = (disk.used / disk.total) * 100
            disk_free_gb = disk.free / (1024 * 1024 * 1024)

            details["disk"] = {
                "usage_percent": round(disk_usage_percent, 2),
                "free_gb": round(disk_free_gb, 2),
                "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
            }

            if disk_usage_percent > 95:
                issues.append(f"Critical disk usage: {disk_usage_percent:.1f}%")
            elif disk_usage_percent > 85:
                issues.append(f"High disk usage: {disk_usage_percent:.1f}%")

            # Process information
            process = psutil.Process()
            details["process"] = {
                "memory_mb": round(process.memory_info().rss / (1024 * 1024), 2),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
            }

            duration_ms = (time.time() - start_time) * 1000

            if not issues:
                return self._create_result(
                    HealthStatus.HEALTHY,
                    "System performance is within normal ranges",
                    details,
                    duration_ms,
                )
            critical_issues = [
                i
                for i in issues
                if "Critical" in i or "High memory" in i or "High CPU" in i
            ]
            status = HealthStatus.CRITICAL if critical_issues else HealthStatus.WARNING
            return self._create_result(
                status,
                f"Performance issues detected: {'; '.join(issues)}",
                details,
                duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return self._create_result(
                HealthStatus.CRITICAL,
                f"Performance health check failed: {e}",
                {"error": str(e)},
                duration_ms,
            )


class ConfigurationHealthCheck(HealthCheck):
    """Health check for configuration system."""

    def __init__(self) -> None:
        super().__init__("Configuration", HealthCheckType.CONFIGURATION)

    def check(self) -> HealthCheckResult:
        """Check configuration system health."""
        start_time = time.time()

        try:
            details: Dict[str, Any] = {}
            issues = []

            # Test configuration manager
            try:
                from claude_builder.core.config import ConfigManager

                config_manager = ConfigManager()
                test_config = config_manager.create_default_config(Path.cwd())

                # Validate configuration
                config_manager._validate_config(test_config)

                details["config_manager"] = {"operational": True}
                details["default_config"] = {"created": True, "valid": True}

            except Exception as e:
                issues.append(f"Configuration manager failed: {e}")
                details["config_manager"] = {"operational": False, "error": str(e)}

            # Check template system availability
            try:
                from claude_builder.core.template_manager import TemplateManager

                template_manager = TemplateManager()
                available_templates = template_manager.list_available_templates()

                details["template_system"] = {
                    "operational": True,
                    "available_templates": len(available_templates),
                }

            except Exception as e:
                issues.append(f"Template system failed: {e}")
                details["template_system"] = {"operational": False, "error": str(e)}

            # Check agent system
            try:
                from claude_builder.core.agents import UniversalAgentSystem

                # Test that agent system can be instantiated
                _ = UniversalAgentSystem()
                details["agent_system"] = {"operational": True}

            except Exception as e:
                issues.append(f"Agent system failed: {e}")
                details["agent_system"] = {"operational": False, "error": str(e)}

            duration_ms = (time.time() - start_time) * 1000

            if not issues:
                return self._create_result(
                    HealthStatus.HEALTHY,
                    "Configuration system is operational",
                    details,
                    duration_ms,
                )
            return self._create_result(
                HealthStatus.CRITICAL,
                f"Configuration issues detected: {'; '.join(issues)}",
                details,
                duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return self._create_result(
                HealthStatus.CRITICAL,
                f"Configuration health check failed: {e}",
                {"error": str(e)},
                duration_ms,
            )


class HealthCheckManager:
    """Central manager for all health checks."""

    def __init__(self, timeout: int = 60) -> None:
        self.timeout = timeout
        self.checks: List[HealthCheck] = []
        self._register_default_checks()

    def _register_default_checks(self) -> None:
        """Register default health checks."""
        self.checks = [
            ApplicationHealthCheck(),
            DependencyHealthCheck(),
            SecurityHealthCheck(),
            PerformanceHealthCheck(),
            ConfigurationHealthCheck(),
        ]

    def add_check(self, check: HealthCheck) -> None:
        """Add a custom health check."""
        self.checks.append(check)

    def remove_check(self, check_name: str) -> bool:
        """Remove a health check by name."""
        for i, check in enumerate(self.checks):
            if check.name == check_name:
                del self.checks[i]
                return True
        return False

    def run_all_checks(self) -> SystemHealth:
        """Run all registered health checks."""
        start_time = time.time()
        results = []

        for check in self.checks:
            try:
                result = check.check()
                results.append(result)
            except Exception as e:
                # Create error result for failed check
                error_result = HealthCheckResult(
                    name=check.name,
                    check_type=check.check_type,
                    status=HealthStatus.CRITICAL,
                    message=f"Health check execution failed: {e}",
                    details={"execution_error": str(e)},
                )
                results.append(error_result)

        # Calculate overall status and statistics
        total_duration_ms = (time.time() - start_time) * 1000

        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.WARNING: 0,
            HealthStatus.CRITICAL: 0,
            HealthStatus.UNKNOWN: 0,
        }

        for result in results:
            status_counts[result.status] += 1

        # Determine overall status
        if status_counts[HealthStatus.CRITICAL] > 0:
            overall_status = HealthStatus.CRITICAL
        elif status_counts[HealthStatus.WARNING] > 0:
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.HEALTHY

        summary = {
            "total_checks": len(results),
            "healthy": status_counts[HealthStatus.HEALTHY],
            "warnings": status_counts[HealthStatus.WARNING],
            "critical": status_counts[HealthStatus.CRITICAL],
            "unknown": status_counts[HealthStatus.UNKNOWN],
            "total_duration_ms": round(total_duration_ms, 2),
        }

        return SystemHealth(
            overall_status=overall_status,
            check_results=results,
            summary=summary,
            total_checks=len(results),
            healthy_checks=status_counts[HealthStatus.HEALTHY],
            warning_checks=status_counts[HealthStatus.WARNING],
            critical_checks=status_counts[HealthStatus.CRITICAL],
            total_duration_ms=total_duration_ms,
        )

    def run_check_by_name(self, check_name: str) -> Optional[HealthCheckResult]:
        """Run a specific health check by name."""
        for check in self.checks:
            if check.name == check_name:
                return check.check()
        return None

    def run_checks_by_type(
        self, check_type: HealthCheckType
    ) -> List[HealthCheckResult]:
        """Run all health checks of a specific type."""
        results = []
        for check in self.checks:
            if check.check_type == check_type:
                try:
                    result = check.check()
                    results.append(result)
                except Exception as e:
                    error_result = HealthCheckResult(
                        name=check.name,
                        check_type=check.check_type,
                        status=HealthStatus.CRITICAL,
                        message=f"Health check execution failed: {e}",
                        details={"execution_error": str(e)},
                    )
                    results.append(error_result)
        return results

    def get_health_report(self) -> Dict[str, Any]:
        """Get a comprehensive health report as dictionary."""
        system_health = self.run_all_checks()

        # Convert to dictionary format for JSON serialization
        checks_list: List[Dict[str, Any]] = []
        report: Dict[str, Any] = {
            "timestamp": system_health.timestamp.isoformat(),
            "overall_status": system_health.overall_status.value,
            "summary": system_health.summary,
            "checks": checks_list,
        }

        for result in system_health.check_results:
            check_data = {
                "name": result.name,
                "type": result.check_type.value,
                "status": result.status.value,
                "message": result.message,
                "details": result.details,
                "timestamp": result.timestamp.isoformat(),
                "duration_ms": result.duration_ms,
            }
            checks_list.append(check_data)

        return report

    def export_health_report(self, output_path: Path, format: str = "json") -> None:
        """Export health report to file."""
        report = self.get_health_report()

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == "json":
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, sort_keys=True)
        else:
            raise ValueError(f"Unsupported export format: {format}")


class HealthMonitor:
    """Continuous health monitoring with alerting."""

    def __init__(self, check_interval: int = 60, alert_threshold: int = 3) -> None:
        self.check_interval = check_interval
        self.alert_threshold = alert_threshold
        self.manager = HealthCheckManager()
        self.is_monitoring = False
        self.failure_count = 0

    def start_monitoring(self) -> None:
        """Start continuous health monitoring."""
        self.is_monitoring = True
        print(f"Health monitoring started (interval: {self.check_interval}s)")

        while self.is_monitoring:
            try:
                health = self.manager.run_all_checks()

                if health.overall_status in [
                    HealthStatus.CRITICAL,
                    HealthStatus.WARNING,
                ]:
                    self.failure_count += 1
                    print(
                        f"Health check failed ({self.failure_count}/{self.alert_threshold}): {health.overall_status.value}"
                    )

                    if self.failure_count >= self.alert_threshold:
                        self._trigger_alert(health)
                        self.failure_count = 0  # Reset after alert
                else:
                    self.failure_count = 0  # Reset on healthy status

                # Wait for next check
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                print("\nHealth monitoring stopped by user")
                break
            except Exception as e:
                print(f"Health monitoring error: {e}")
                time.sleep(self.check_interval)

        self.is_monitoring = False

    def stop_monitoring(self) -> None:
        """Stop continuous health monitoring."""
        self.is_monitoring = False

    def _trigger_alert(self, health: SystemHealth) -> None:
        """Trigger health alert."""
        timestamp = datetime.now().isoformat()
        print(f"\n🚨 HEALTH ALERT - {timestamp}")
        print(f"Overall Status: {health.overall_status.value.upper()}")
        print(f"Critical Checks: {health.critical_checks}")
        print(f"Warning Checks: {health.warning_checks}")

        for result in health.check_results:
            if result.status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
                print(f"  - {result.name}: {result.status.value} - {result.message}")
        print()
