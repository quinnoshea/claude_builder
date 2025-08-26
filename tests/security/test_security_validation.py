"""Security validation tests for Claude Builder.

This test suite validates all security fixes implemented in the emergency
security response, including path traversal, SSRF, and zip bomb protection.
"""

import tempfile
import zipfile

from pathlib import Path
from unittest.mock import patch

import pytest

from claude_builder.utils.exceptions import SecurityError
from claude_builder.utils.security import SecurityValidator, security_validator


class TestSecurityValidator:
    """Test the SecurityValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SecurityValidator()

    def test_validate_url_https_allowed(self):
        """Test that HTTPS URLs from whitelisted domains are allowed."""
        valid_urls = [
            "https://raw.githubusercontent.com/user/repo/main/file.json",
            "https://github.com/user/repo",
            "https://api.github.com/repos/user/repo",
        ]

        for url in valid_urls:
            assert self.validator.validate_url(url) is True

    def test_validate_url_http_blocked(self):
        """Test that HTTP URLs are blocked (only HTTPS allowed)."""
        http_urls = [
            "http://github.com/user/repo",
            "http://raw.githubusercontent.com/user/repo/main/file.json",
        ]

        for url in http_urls:
            with pytest.raises(SecurityError, match="Only HTTPS protocol allowed"):
                self.validator.validate_url(url)

    def test_validate_url_non_whitelisted_domain_blocked(self):
        """Test that non-whitelisted domains are blocked."""
        malicious_urls = [
            "https://evil.com/malicious.zip",
            "https://attacker.net/payload.json",
            "https://malware-site.org/backdoor.exe",
        ]

        for url in malicious_urls:
            with pytest.raises(SecurityError, match="Domain not whitelisted"):
                self.validator.validate_url(url)

    def test_validate_url_private_ip_blocked(self):
        """Test that private IP addresses are blocked (SSRF protection)."""
        private_ips = [
            "https://127.0.0.1/admin",
            "https://10.0.0.1/internal",
            "https://192.168.1.1/router",
            "https://172.16.0.1/private",
        ]

        for url in private_ips:
            with pytest.raises(
                SecurityError, match="(IP address blocked|Direct IP access not allowed)"
            ):
                self.validator.validate_url(url)

    def test_validate_url_invalid_port_blocked(self):
        """Test that non-standard ports are blocked."""
        port_urls = [
            "https://github.com:8080/repo",
            "https://raw.githubusercontent.com:3000/file",
        ]

        for url in port_urls:
            with pytest.raises(SecurityError, match="Non-standard port not allowed"):
                self.validator.validate_url(url)

    def test_validate_file_path_traversal_blocked(self):
        """Test that path traversal attempts are blocked."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config",
            "templates/../../../secret.key",
            "valid/../../../etc/shadow",
            "....//....//etc/passwd",
        ]

        for path in malicious_paths:
            with pytest.raises(SecurityError, match="Path traversal detected"):
                self.validator.validate_file_path(path)

    def test_validate_file_path_absolute_blocked(self):
        """Test that absolute paths are blocked."""
        absolute_paths = [
            "/etc/passwd",
            "/home/user/.ssh/id_rsa",
            "C:\\Windows\\System32\\config",
            "/var/log/secure",
        ]

        for path in absolute_paths:
            with pytest.raises(SecurityError, match="Absolute paths not allowed"):
                self.validator.validate_file_path(path)

    def test_validate_file_path_null_byte_blocked(self):
        """Test that null byte injection is blocked."""
        null_byte_paths = [
            "template.json\x00.exe",
            "safe_file\x00../../../etc/passwd",
            "template\x00.bat",
        ]

        for path in null_byte_paths:
            with pytest.raises(SecurityError, match="Null byte detected"):
                self.validator.validate_file_path(path)

    def test_validate_file_path_safe_paths_allowed(self):
        """Test that safe relative paths are allowed."""
        safe_paths = [
            "template.json",
            "templates/python/django.md",
            "base/README.md",
            "custom-template.zip",
        ]

        for path in safe_paths:
            assert self.validator.validate_file_path(path) is True

    def test_validate_file_content_dangerous_patterns_blocked(self):
        """Test that dangerous content patterns are blocked."""
        dangerous_contents = [
            '<script>alert("xss")</script>',
            'javascript:alert("malicious")',
            'eval("dangerous_code()")',
            'exec("rm -rf /")',
            'os.system("malicious_command")',
            '__import__("subprocess")',
        ]

        for content in dangerous_contents:
            with pytest.raises(SecurityError, match="Dangerous content pattern"):
                self.validator.validate_file_content(content, "test.md")

    def test_validate_file_content_blocked_extensions(self):
        """Test that blocked file extensions raise security errors."""
        blocked_extensions = [
            ("content", "malware.exe"),
            ("content", "script.bat"),
            ("content", "payload.ps1"),
            ("content", "virus.com"),
        ]

        for content, filepath in blocked_extensions:
            with pytest.raises(SecurityError, match="Blocked file extension"):
                self.validator.validate_file_content(content, filepath)

    def test_validate_template_metadata_sanitization(self):
        """Test that template metadata is properly sanitized."""
        malicious_metadata = {
            "name": '<script>alert("xss")</script>template',
            "description": "Malicious template with <script>evil()</script>",
            "author": "Attacker<script>steal_data()</script>",
            "unknown_field": "should be filtered out",
            "tags": ["<script>tag</script>", "normal_tag"],
        }

        safe_metadata = self.validator.validate_template_metadata(malicious_metadata)

        # Check that HTML is escaped and unknown fields are filtered
        assert "<script>" not in safe_metadata["name"]
        assert "<script>" not in safe_metadata["description"]
        assert "<script>" not in safe_metadata["author"]
        assert "unknown_field" not in safe_metadata
        assert len(safe_metadata["tags"]) == 2


class TestZipSecurity:
    """Test zip file security validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SecurityValidator()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def create_safe_zip(self) -> Path:
        """Create a safe test zip file."""
        zip_path = self.temp_path / "safe.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("template.json", '{"name": "test", "version": "1.0.0"}')
            zf.writestr("README.md", "# Test Template")
            zf.writestr("templates/base.md", "# Base Template")
        return zip_path

    def create_path_traversal_zip(self) -> Path:
        """Create a zip with path traversal attack."""
        zip_path = self.temp_path / "traversal.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            # Try to write outside the extraction directory
            zf.writestr("../../../etc/passwd", "root:x:0:0:root:/root:/bin/bash")
            zf.writestr("..\\..\\windows\\system32\\malicious.exe", "malware")
        return zip_path

    def create_zip_bomb(self) -> Path:
        """Create a zip bomb (highly compressed malicious file)."""
        zip_path = self.temp_path / "bomb.zip"

        # Create a large file content (1MB of zeros)
        large_content = b"0" * (1024 * 1024)

        with zipfile.ZipFile(
            zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as zf:
            # Add multiple large files to exceed size limits
            for i in range(200):  # 200MB total when extracted
                zf.writestr(f"large_file_{i}.txt", large_content)

        return zip_path

    def test_safe_zip_validation_passes(self):
        """Test that safe zip files pass validation."""
        zip_path = self.create_safe_zip()
        assert self.validator.validate_zip_file(zip_path) is True

    def test_path_traversal_zip_blocked(self):
        """Test that path traversal in zip files is blocked."""
        zip_path = self.create_path_traversal_zip()

        with pytest.raises(SecurityError, match="Path traversal detected"):
            self.validator.validate_zip_file(zip_path)

    def test_zip_bomb_blocked(self):
        """Test that zip bombs are detected and blocked."""
        zip_path = self.create_zip_bomb()

        with pytest.raises(SecurityError, match="Total extracted size too large"):
            self.validator.validate_zip_file(zip_path)

    def test_safe_zip_extraction(self):
        """Test that safe zip extraction works correctly."""
        zip_path = self.create_safe_zip()
        extract_path = self.temp_path / "extracted"

        # Should extract without errors
        self.validator.safe_extract_zip(zip_path, extract_path)

        # Verify files were extracted
        assert (extract_path / "template.json").exists()
        assert (extract_path / "README.md").exists()
        assert (extract_path / "templates" / "base.md").exists()

    def test_malicious_zip_extraction_blocked(self):
        """Test that malicious zip extraction is blocked."""
        zip_path = self.create_path_traversal_zip()
        extract_path = self.temp_path / "extracted"

        with pytest.raises(SecurityError):
            self.validator.safe_extract_zip(zip_path, extract_path)


class TestTemplateManagerSecurity:
    """Test security fixes in TemplateManager."""

    @patch("claude_builder.core.template_manager.urlopen")
    def test_download_file_url_validation(self, mock_urlopen):
        """Test that _download_file validates URLs before downloading."""
        from claude_builder.core.template_manager import TemplateManager

        manager = TemplateManager()
        temp_file = Path(tempfile.mktemp(suffix=".zip"))

        # Test blocked domain
        with pytest.raises(SecurityError, match="Domain not whitelisted"):
            manager._download_file("https://evil.com/malware.zip", temp_file)

        # Test HTTP protocol blocked
        with pytest.raises(SecurityError, match="Only HTTPS protocol allowed"):
            manager._download_file("http://github.com/repo.zip", temp_file)

        # Ensure urlopen was never called for blocked URLs
        mock_urlopen.assert_not_called()

    @patch("claude_builder.core.template_manager.urlopen")
    def test_fetch_templates_url_validation(self, mock_urlopen):
        """Test that template source fetching validates URLs."""
        from claude_builder.core.template_manager import TemplateManager

        manager = TemplateManager()

        # Test blocked domain
        templates = manager._fetch_templates_from_source("https://evil.com/")
        assert len(templates) == 0  # Should return empty list due to blocked domain

        # Ensure urlopen was never called
        mock_urlopen.assert_not_called()

    def test_template_metadata_validation(self):
        """Test that template metadata goes through security validation."""
        from claude_builder.core.template_manager import TemplateMetadata

        malicious_data = {
            "name": '<script>alert("xss")</script>malicious',
            "description": "Evil template",
            "author": "Attacker",
            "version": "1.0.0",
        }

        # TemplateMetadata should handle the data safely
        # (The security validation happens in _fetch_templates_from_source)
        metadata = TemplateMetadata(malicious_data)

        # The name should contain the malicious script (validation happens upstream)
        assert metadata.name == '<script>alert("xss")</script>malicious'


class TestSecurityIntegration:
    """Integration tests for security features."""

    def test_global_security_validator_available(self):
        """Test that global security validator is available."""
        assert security_validator is not None
        assert isinstance(security_validator, SecurityValidator)

    def test_security_error_hierarchy(self):
        """Test that SecurityError properly inherits from base exceptions."""
        error = SecurityError("Test security violation")
        assert isinstance(error, Exception)
        assert error.exit_code == 3
        assert "security violation" in str(error).lower()


@pytest.fixture
def sample_template_data():
    """Sample template metadata for testing."""
    return {
        "name": "test-template",
        "version": "1.0.0",
        "description": "A test template",
        "author": "Test Author",
        "category": "testing",
        "tags": ["test", "sample"],
        "languages": ["python"],
        "frameworks": ["django"],
        "project_types": ["web"],
        "license": "MIT",
    }


@pytest.fixture
def malicious_template_data():
    """Malicious template metadata for testing."""
    return {
        "name": '<script>alert("xss")</script>evil-template',
        "description": 'Evil template with javascript:alert("malicious") code',
        "author": "Attacker<script>steal_credentials()</script>",
        "evil_field": "should_be_filtered",
        "tags": ["<script>malicious</script>", "normal"],
        "version": "1.0.0",
    }


class TestSecurityFixValidation:
    """Validate that all security fixes are working correctly."""

    def test_all_critical_vulnerabilities_fixed(self):
        """Comprehensive test that all critical vulnerabilities are fixed."""
        validator = SecurityValidator()

        # Path traversal protection
        with pytest.raises(SecurityError):
            validator.validate_file_path("../../../etc/passwd")

        # URL validation with whitelist
        with pytest.raises(SecurityError):
            validator.validate_url("https://evil.com/malware.zip")

        # Content validation
        with pytest.raises(SecurityError):
            validator.validate_file_content("<script>evil()</script>", "test.html")

        # Zip validation would require creating actual zip files
        # (covered in TestZipSecurity)

        # All tests passing means critical vulnerabilities are fixed
        assert True, "All critical security vulnerabilities have been addressed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
