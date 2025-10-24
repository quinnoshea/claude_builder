"""Secure storage utilities for sensitive data like tokens and credentials.

This module provides encrypted storage for sensitive information using
industry-standard cryptographic libraries and secure key management.
"""

import logging
import os

from getpass import getpass
from pathlib import Path
from typing import Any, Dict, Optional, Union


try:
    import base64

    import keyring

    from cryptography.fernet import Fernet

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

import contextlib

from claude_builder.utils.exceptions import SecurityError


class SecureTokenManager:
    """Secure token management with encryption and keyring integration."""

    def __init__(self, service_name: str = "claude-builder"):
        """Initialize secure token manager.

        Args:
            service_name: Service name for keyring storage

        Raises:
            SecurityError: If cryptography libraries are not available
        """
        if not CRYPTO_AVAILABLE:
            msg = (
                "Cryptography libraries required for secure storage are not available. "
                "Please install with: pip install cryptography keyring"
            )
            raise SecurityError(msg)

        self.service_name = service_name
        self.logger = logging.getLogger(__name__)
        self._fernet: Optional[Fernet] = None

    def _get_or_create_encryption_key(self) -> Fernet:
        """Get or create encryption key for token storage."""
        if self._fernet is not None:
            return self._fernet

        try:
            # Try to get existing key from keyring
            key_data = keyring.get_password(self.service_name, "encryption_key")

            if key_data:
                self.logger.debug("Retrieved existing encryption key from keyring")
                key = key_data.encode()
            else:
                # Generate new key
                self.logger.info("Generating new encryption key for secure storage")
                key = Fernet.generate_key()

                # Store in keyring
                keyring.set_password(self.service_name, "encryption_key", key.decode())
                self.logger.debug("Stored new encryption key in keyring")

            self._fernet = Fernet(key)
            return self._fernet

        except Exception as e:
            msg = f"Failed to initialize encryption key: {e}"
            raise SecurityError(msg) from e

    def store_token(self, token_name: str, token_value: str) -> None:
        """Store an encrypted token.

        Args:
            token_name: Name/identifier for the token
            token_value: The token value to encrypt and store

        Raises:
            SecurityError: If encryption or storage fails
        """
        try:
            if not token_value or not token_value.strip():
                msg = "Cannot store empty token"
                raise SecurityError(msg)

            # Get encryption key
            fernet = self._get_or_create_encryption_key()

            # Encrypt the token
            encrypted_token = fernet.encrypt(token_value.encode())

            # Store in keyring
            keyring.set_password(
                self.service_name, f"token_{token_name}", encrypted_token.decode()
            )

            self.logger.info(f"Successfully stored encrypted token: {token_name}")

        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            msg = f"Failed to store token {token_name}: {e}"
            raise SecurityError(msg) from e

    def get_token(
        self, token_name: str, prompt_if_missing: bool = True
    ) -> Optional[str]:
        """Retrieve and decrypt a stored token.

        Args:
            token_name: Name/identifier for the token
            prompt_if_missing: Whether to prompt user if token is not found

        Returns:
            Decrypted token value or None if not found

        Raises:
            SecurityError: If decryption fails
        """
        try:
            # Try to get encrypted token from keyring
            encrypted_token = keyring.get_password(
                self.service_name, f"token_{token_name}"
            )

            if encrypted_token:
                # Decrypt the token
                fernet = self._get_or_create_encryption_key()
                decrypted_token: str = fernet.decrypt(encrypted_token.encode()).decode()

                self.logger.debug(f"Successfully retrieved token: {token_name}")
                return decrypted_token

            if prompt_if_missing:
                # Token not found, prompt user
                self.logger.info(f"Token {token_name} not found, prompting user")
                token_value = getpass(f"Enter {token_name} token: ")

                if token_value and token_value.strip():
                    # Store for future use
                    self.store_token(token_name, token_value)
                    return token_value

            return None

        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            msg = f"Failed to retrieve token {token_name}: {e}"
            raise SecurityError(msg) from e

    def delete_token(self, token_name: str) -> bool:
        """Delete a stored token.

        Args:
            token_name: Name/identifier for the token

        Returns:
            True if token was deleted, False if not found
        """
        try:
            # Try to delete from keyring
            keyring.delete_password(self.service_name, f"token_{token_name}")
            self.logger.info(f"Deleted token: {token_name}")
            return True

        except keyring.errors.PasswordDeleteError:
            self.logger.warning(f"Token {token_name} not found for deletion")
            return False
        except Exception as e:
            self.logger.exception(f"Error deleting token {token_name}: {e}")
            msg = f"Failed to delete token {token_name}: {e}"
            raise SecurityError(msg) from e

    def list_stored_tokens(self) -> list[str]:
        """List all stored token names.

        Returns:
            List of token names (without the 'token_' prefix)
        """
        # Note: keyring doesn't provide a direct way to list all keys
        # This is a limitation of the keyring interface
        # In practice, applications should track their own token names
        self.logger.warning("Token listing not supported by keyring interface")
        return []

    def rotate_encryption_key(self) -> None:
        """Rotate the encryption key (re-encrypt all tokens with new key).

        Warning: This will require re-entering all tokens as keyring doesn't
        provide a way to list existing keys.
        """
        try:
            # Delete old encryption key
            with contextlib.suppress(keyring.errors.PasswordDeleteError):
                keyring.delete_password(self.service_name, "encryption_key")

            # Clear cached key to force regeneration
            self._fernet = None

            self.logger.info(
                "Encryption key rotated - tokens will need to be re-entered"
            )

        except Exception as e:
            msg = f"Failed to rotate encryption key: {e}"
            raise SecurityError(msg) from e


class FallbackSecureStorage:
    """Fallback secure storage when keyring/cryptography not available."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize fallback storage.

        Args:
            storage_dir: Directory for storing encrypted files
        """
        self.storage_dir = storage_dir or Path.home() / ".claude-builder" / "secure"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Warn about reduced security
        self.logger.warning(
            "Using fallback storage - install 'cryptography' and 'keyring' "
            "packages for enhanced security"
        )

    def store_token(self, token_name: str, token_value: str) -> None:
        """Store token with basic encoding (NOT secure encryption)."""
        if not token_value or not token_value.strip():
            msg = "Cannot store empty token"
            raise SecurityError(msg)

        # Basic base64 encoding (NOT secure - just obfuscation)
        encoded_token = base64.b64encode(token_value.encode()).decode()

        token_file = self.storage_dir / f"{token_name}.token"
        token_file.write_text(encoded_token, encoding="utf-8")

        # Set restrictive permissions (Unix only)
        if os.name != "nt":
            token_file.chmod(0o600)

        self.logger.warning(
            f"Stored token {token_name} with basic encoding (not encrypted)"
        )

    def get_token(
        self, token_name: str, prompt_if_missing: bool = True
    ) -> Optional[str]:
        """Retrieve token with basic decoding."""
        token_file = self.storage_dir / f"{token_name}.token"

        if token_file.exists():
            try:
                encoded_token = token_file.read_text(encoding="utf-8").strip()
                return base64.b64decode(encoded_token).decode()
            except Exception as e:
                msg = f"Failed to decode token {token_name}: {e}"
                raise SecurityError(msg) from e

        elif prompt_if_missing:
            token_value = getpass(f"Enter {token_name} token: ")
            if token_value and token_value.strip():
                self.store_token(token_name, token_value)
                return token_value

        return None

    def delete_token(self, token_name: str) -> bool:
        """Delete a stored token file."""
        token_file = self.storage_dir / f"{token_name}.token"
        if token_file.exists():
            token_file.unlink()
            return True
        return False

    def list_stored_tokens(self) -> list[str]:
        """List stored token files."""
        return [f.stem for f in self.storage_dir.glob("*.token")]


class SecureConfigManager:
    """Secure configuration manager with encrypted sensitive fields."""

    def __init__(self, config_name: str = "claude-builder"):
        """Initialize secure configuration manager."""
        self.config_name = config_name
        self.logger = logging.getLogger(__name__)

        # Initialize appropriate storage backend
        if CRYPTO_AVAILABLE:
            self.token_manager: Union[SecureTokenManager, FallbackSecureStorage] = (
                SecureTokenManager(config_name)
            )
        else:
            self.token_manager = FallbackSecureStorage()

    def store_secure_config(self, config_data: Dict[str, Any]) -> None:
        """Store configuration with encrypted sensitive fields.

        Args:
            config_data: Configuration dictionary with sensitive fields
        """
        sensitive_fields = {
            "github_token",
            "api_key",
            "password",
            "secret",
            "token",
            "access_token",
            "refresh_token",
            "private_key",
        }

        for key, value in config_data.items():
            if any(field in key.lower() for field in sensitive_fields):
                if isinstance(value, str) and value.strip():
                    self.token_manager.store_token(key, value)
                    self.logger.info(f"Stored sensitive config field: {key}")

    def get_secure_config(
        self, field_name: str, prompt_if_missing: bool = False
    ) -> Optional[str]:
        """Get encrypted configuration field.

        Args:
            field_name: Name of the configuration field
            prompt_if_missing: Whether to prompt if field is missing

        Returns:
            Decrypted field value or None
        """
        result = self.token_manager.get_token(field_name, prompt_if_missing)
        return result if isinstance(result, (str, type(None))) else str(result)

    def delete_secure_config(self, field_name: str) -> bool:
        """Delete encrypted configuration field."""
        return self.token_manager.delete_token(field_name)


# Global instances for easy access
if CRYPTO_AVAILABLE:
    default_token_manager: Union[SecureTokenManager, FallbackSecureStorage] = (
        SecureTokenManager()
    )
    default_config_manager: Optional[SecureConfigManager] = SecureConfigManager()
else:
    default_token_manager = FallbackSecureStorage()
    default_config_manager = None


def get_github_token() -> Optional[str]:
    """Convenience function to get GitHub token."""
    return default_token_manager.get_token("github_token", prompt_if_missing=False)


def store_github_token(token: str) -> None:
    """Convenience function to store GitHub token."""
    default_token_manager.store_token("github_token", token)


def is_secure_storage_available() -> bool:
    """Check if secure storage (keyring + cryptography) is available."""
    return CRYPTO_AVAILABLE
