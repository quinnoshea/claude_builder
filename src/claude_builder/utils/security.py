"""Security utilities for Claude Builder.

This module provides comprehensive security validation and protection
against common vulnerabilities including path traversal, SSRF, and
malicious content injection.
"""

import html
import ipaddress
import os
import re
import zipfile

from pathlib import Path
from typing import List, Optional, Pattern, Set
from urllib.parse import urlparse

from claude_builder.utils.exceptions import SecurityError


# Allowed domains for external requests (whitelist approach)
ALLOWED_DOMAINS: Set[str] = {
    "raw.githubusercontent.com",
    "github.com",
    "api.github.com",
    "cdn.jsdelivr.net",
    "unpkg.com",
}

# Blocked IP ranges for SSRF protection
BLOCKED_IP_RANGES = [
    ipaddress.IPv4Network("10.0.0.0/8"),  # Private
    ipaddress.IPv4Network("172.16.0.0/12"),  # Private
    ipaddress.IPv4Network("192.168.0.0/16"),  # Private
    ipaddress.IPv4Network("127.0.0.0/8"),  # Loopback
    ipaddress.IPv4Network("169.254.0.0/16"),  # Link-local
    ipaddress.IPv4Network("224.0.0.0/4"),  # Multicast
    ipaddress.IPv4Network("240.0.0.0/4"),  # Reserved
]

# File extension blacklist
BLOCKED_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".scr",
    ".vbs",
    ".ps1",
    ".com",
    ".pif",
    ".msi",
    ".reg",
    ".jar",
    ".app",
}

# Dangerous content patterns
DANGEROUS_PATTERNS: List[Pattern] = [
    re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"data:text/html", re.IGNORECASE),
    re.compile(r"vbscript:", re.IGNORECASE),
    re.compile(r"eval\s*\(", re.IGNORECASE),
    re.compile(r"exec\s*\(", re.IGNORECASE),
    re.compile(r"system\s*\(", re.IGNORECASE),
    re.compile(r"os\.system", re.IGNORECASE),
    re.compile(r"subprocess\.", re.IGNORECASE),
    re.compile(r"__import__", re.IGNORECASE),
]

# Maximum file sizes (in bytes)
MAX_TEMPLATE_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_ZIP_SIZE = 50 * 1024 * 1024  # 50MB
MAX_EXTRACTED_SIZE = 100 * 1024 * 1024  # 100MB


class SecurityValidator:
    """Comprehensive security validation for Claude Builder operations."""

    def __init__(self) -> None:
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []

    def validate_url(self, url: str) -> bool:
        """Validate URL against SSRF and domain restrictions.

        Args:
            url: URL to validate

        Returns:
            True if URL is safe

        Raises:
            SecurityError: If URL is unsafe
        """
        try:
            parsed = urlparse(url)

            # Protocol validation - only allow HTTPS (more secure)
            if parsed.scheme not in ("https",):
                msg = f"Only HTTPS protocol allowed, got: {parsed.scheme}"
                raise SecurityError(msg)

            # Hostname validation
            if not parsed.hostname:
                msg = "URL must have a valid hostname"
                raise SecurityError(msg)

            # IP address blocking first (prevent direct IP access)
            try:
                ip = ipaddress.ip_address(parsed.hostname)
                for blocked_range in BLOCKED_IP_RANGES:
                    if ip in blocked_range:
                        msg = f"IP address blocked: {ip}"
                        raise SecurityError(msg)
                # If IP is not in blocked ranges but is an IP, still block it
                msg = f"Direct IP access not allowed: {ip}"
                raise SecurityError(msg)
            except ValueError:
                # Not an IP address, continue with domain validation
                pass

            # Domain whitelist check
            if parsed.hostname not in ALLOWED_DOMAINS:
                msg = f"Domain not whitelisted: {parsed.hostname}"
                raise SecurityError(msg)

            # Port validation (only standard ports)
            if parsed.port and parsed.port not in (80, 443):
                msg = f"Non-standard port not allowed: {parsed.port}"
                raise SecurityError(msg)

            return True

        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            msg = f"URL validation failed: {e}"
            raise SecurityError(msg) from e

    def validate_file_path(
        self, file_path: str, base_path: Optional[str] = None
    ) -> bool:
        """Validate file paths against directory traversal attacks.

        Args:
            file_path: Path to validate
            base_path: Optional base path to restrict access to

        Returns:
            True if path is safe

        Raises:
            SecurityError: If path is unsafe
        """
        # Normalize the path to handle .. and other traversal attempts
        normalized = os.path.normpath(file_path)

        # Check for null bytes first (path injection)
        if "\x00" in file_path:
            msg = f"Null byte detected in path: {file_path}"
            raise SecurityError(msg)

        # Check for directory traversal patterns
        if ".." in normalized:
            msg = f"Path traversal detected: {file_path}"
            raise SecurityError(msg)

        # Check for absolute paths (should be relative)
        # Check both Unix and Windows absolute path patterns
        if os.path.isabs(normalized) or (
            len(normalized) >= 3
            and normalized[1] == ":"
            and normalized[2] in ("\\", "/")
        ):
            msg = f"Absolute paths not allowed: {file_path}"
            raise SecurityError(msg)

        # If base_path provided, ensure resolved path is within base
        if base_path:
            base_resolved = Path(base_path).resolve()
            try:
                full_path = base_resolved / normalized
                full_resolved = full_path.resolve()

                # Check if the resolved path is within the base directory
                if not str(full_resolved).startswith(str(base_resolved)):
                    msg = f"Path escapes base directory: {file_path}"
                    raise SecurityError(msg)
            except (OSError, ValueError) as e:
                msg = f"Path validation failed: {e}"
                raise SecurityError(msg) from e

        return True

    def validate_file_content(self, content: str, file_path: str) -> str:
        """Sanitize and validate file content for security.

        Args:
            content: File content to validate
            file_path: Path of the file (for context)

        Returns:
            Sanitized content

        Raises:
            SecurityError: If content contains dangerous patterns
        """
        # Check file extension
        file_path_lower = file_path.lower()
        if any(file_path_lower.endswith(ext) for ext in BLOCKED_EXTENSIONS):
            msg = f"Blocked file extension: {file_path}"
            raise SecurityError(msg)

        # Check for dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if pattern.search(content):
                msg = f"Dangerous content pattern detected in {file_path}: {pattern.pattern}"
                raise SecurityError(msg)

        # HTML escape content for template files
        if file_path_lower.endswith((".md", ".txt", ".html")):
            # Only escape if content looks like it might have HTML
            if any(char in content for char in "<>&\"'"):
                # Be selective about HTML escaping for markdown files
                if file_path_lower.endswith(".html"):
                    content = html.escape(content)

        return content

    def validate_zip_file(self, zip_path: Path, max_size: int = MAX_ZIP_SIZE) -> bool:
        """Validate zip file for security issues.

        Args:
            zip_path: Path to zip file
            max_size: Maximum allowed zip size

        Returns:
            True if zip file is safe

        Raises:
            SecurityError: If zip file is unsafe
        """
        # Check zip file size
        if zip_path.stat().st_size > max_size:
            msg = f"Zip file too large: {zip_path.stat().st_size} > {max_size}"
            raise SecurityError(msg)

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_file:
                # Check for zip bomb (excessive compression ratio)
                total_size = 0
                for info in zip_file.infolist():
                    total_size += info.file_size

                    # Individual file size check
                    if info.file_size > MAX_TEMPLATE_FILE_SIZE:
                        msg = f"File too large in zip: {info.filename} ({info.file_size} bytes)"
                        raise SecurityError(msg)

                    # Path validation for each file
                    self.validate_file_path(info.filename)

                # Total extracted size check
                if total_size > MAX_EXTRACTED_SIZE:
                    msg = f"Total extracted size too large: {total_size}"
                    raise SecurityError(msg)

                # Compression ratio check (potential zip bomb)
                compressed_size = zip_path.stat().st_size
                if compressed_size > 0:
                    ratio = total_size / compressed_size
                    if ratio > 100:  # More than 100:1 compression ratio is suspicious
                        msg = f"Suspicious compression ratio: {ratio}"
                        raise SecurityError(msg)

        except zipfile.BadZipFile as e:
            msg = f"Invalid zip file: {e}"
            raise SecurityError(msg) from e

        return True

    def safe_extract_zip(self, zip_path: Path, extract_path: Path) -> None:
        """Safely extract a zip file with security validations.

        Args:
            zip_path: Path to zip file
            extract_path: Directory to extract to

        Raises:
            SecurityError: If extraction would be unsafe
        """
        # Validate zip file first
        self.validate_zip_file(zip_path)

        # Ensure extract path exists and is a directory
        extract_path.mkdir(parents=True, exist_ok=True)
        extract_resolved = extract_path.resolve()

        with zipfile.ZipFile(zip_path, "r") as zip_file:
            for member in zip_file.infolist():
                # Validate each member path
                self.validate_file_path(member.filename)

                # Calculate target path
                target_path = extract_path / member.filename
                target_resolved = target_path.resolve()

                # Ensure target is within extract directory
                if not str(target_resolved).startswith(str(extract_resolved)):
                    msg = f"Zip member would extract outside target: {member.filename}"
                    raise SecurityError(msg)

                # Extract the member
                zip_file.extract(member, extract_path)

    def validate_template_metadata(self, metadata: dict) -> dict:
        """Validate and sanitize template metadata.

        Args:
            metadata: Raw metadata dictionary

        Returns:
            Sanitized metadata dictionary

        Raises:
            SecurityError: If metadata contains unsafe content
        """
        safe_metadata = {}

        # Define allowed keys and their types
        allowed_keys = {
            "name": str,
            "version": str,
            "description": str,
            "author": str,
            "category": str,
            "tags": list,
            "languages": list,
            "frameworks": list,
            "project_types": list,
            "min_builder_version": str,
            "homepage": str,
            "repository": str,
            "license": str,
            "created": str,
            "updated": str,
        }

        for key, value in metadata.items():
            if key not in allowed_keys:
                self.validation_warnings.append(f"Unknown metadata key ignored: {key}")
                continue

            expected_type = allowed_keys[key]
            if not isinstance(value, expected_type):
                if expected_type == str and value is not None:
                    value = str(value)
                elif expected_type == list and value is not None:
                    value = [value] if isinstance(value, str) else list(value)
                else:
                    self.validation_warnings.append(
                        f"Invalid type for {key}: expected {expected_type.__name__}"
                    )
                    continue

            # Sanitize string values
            if isinstance(value, str):
                value = self._sanitize_string(value)
                # Validate URLs if applicable
                if key in ("homepage", "repository") and value:
                    try:
                        # More lenient validation for metadata URLs
                        parsed = urlparse(value)
                        if parsed.scheme not in ("http", "https"):
                            self.validation_warnings.append(
                                f"Non-HTTP URL in {key}: {value}"
                            )
                    except Exception:
                        self.validation_warnings.append(
                            f"Invalid URL in {key}: {value}"
                        )
            elif isinstance(value, list):
                value = [self._sanitize_string(str(item)) for item in value]

            safe_metadata[key] = value

        return safe_metadata

    def _sanitize_string(self, text: str) -> str:
        """Sanitize a string value."""
        if not text:
            return text

        # Remove null bytes
        text = text.replace("\x00", "")

        # Basic HTML escape for safety
        text = html.escape(text, quote=False)

        # Limit length
        if len(text) > 1000:
            text = text[:1000] + "..."

        return text.strip()


# Global security validator instance
security_validator = SecurityValidator()
