"""Secure credential storage using system keyring and encrypted fallback."""

import logging
from typing import Optional
import keyring
from keyring.errors import KeyringError, NoKeyringError
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os

logger = logging.getLogger(__name__)

# Application identifier for keyring
SERVICE_NAME = "whatnow"

# Credential keys
KEY_GITHUB_TOKEN = "github_token"
KEY_ENCRYPTION_KEY = "encryption_key"


class CredentialStore:
    """Secure credential storage with system keyring and encrypted fallback.

    Attempts to use system keyring (most secure). If unavailable,
    falls back to encrypted storage in the database.
    """

    def __init__(self, db=None):
        """Initialize credential store.

        Args:
            db: Database instance for fallback encrypted storage
        """
        self.db = db
        self._keyring_available = self._check_keyring()
        self._encryption_key: Optional[bytes] = None

        if not self._keyring_available and db:
            logger.warning(
                "System keyring not available, using encrypted database fallback"
            )
            self._init_encryption()

    def _check_keyring(self) -> bool:
        """Check if system keyring is available and working.

        Returns:
            True if keyring is available, False otherwise
        """
        try:
            # Try to get keyring backend
            backend = keyring.get_keyring()
            if backend is None:
                return False

            # Test if we can actually use it
            test_key = "_whatnow_test"
            test_value = "test"

            # Try to set and get a test value
            keyring.set_password(SERVICE_NAME, test_key, test_value)
            result = keyring.get_password(SERVICE_NAME, test_key)

            # Clean up test
            try:
                keyring.delete_password(SERVICE_NAME, test_key)
            except Exception:
                pass

            return result == test_value

        except (KeyringError, NoKeyringError, Exception) as e:
            logger.debug(f"Keyring not available: {e}")
            return False

    def _init_encryption(self):
        """Initialize encryption key for fallback storage."""
        if not self.db:
            raise RuntimeError("Database required for encrypted fallback storage")

        # Try to get existing encryption key from keyring first
        if self._keyring_available:
            try:
                key_str = keyring.get_password(SERVICE_NAME, KEY_ENCRYPTION_KEY)
                if key_str:
                    self._encryption_key = key_str.encode()
                    return
            except Exception as e:
                logger.debug(f"Could not get encryption key from keyring: {e}")

        # Generate or retrieve encryption key from database
        key_config = self.db.get_config("_encryption_key")
        if key_config:
            self._encryption_key = key_config.encode()
        else:
            # Generate new encryption key
            self._encryption_key = Fernet.generate_key()
            self.db.set_config("_encryption_key", self._encryption_key.decode())
            logger.info("Generated new encryption key for credential storage")

    def _encrypt(self, value: str) -> str:
        """Encrypt a value for database storage.

        Args:
            value: Plain text value

        Returns:
            Encrypted value as base64 string
        """
        if not self._encryption_key:
            raise RuntimeError("Encryption not initialized")

        fernet = Fernet(self._encryption_key)
        encrypted = fernet.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()

    def _decrypt(self, encrypted_value: str) -> str:
        """Decrypt a value from database storage.

        Args:
            encrypted_value: Encrypted value as base64 string

        Returns:
            Decrypted plain text value
        """
        if not self._encryption_key:
            raise RuntimeError("Encryption not initialized")

        fernet = Fernet(self._encryption_key)
        encrypted = base64.b64decode(encrypted_value.encode())
        return fernet.decrypt(encrypted).decode()

    def set_credential(self, key: str, value: str):
        """Store a credential securely.

        Args:
            key: Credential identifier
            value: Credential value
        """
        if not value:
            # Empty value, delete the credential
            self.delete_credential(key)
            return

        if self._keyring_available:
            try:
                keyring.set_password(SERVICE_NAME, key, value)
                logger.debug(f"Stored credential '{key}' in system keyring")
                return
            except Exception as e:
                logger.warning(f"Failed to store in keyring, using fallback: {e}")

        # Fallback to encrypted database storage
        if not self.db:
            raise RuntimeError("No secure storage available")

        encrypted = self._encrypt(value)
        db_key = f"_secure_{key}"
        self.db.set_config(db_key, encrypted)
        logger.debug(f"Stored credential '{key}' in encrypted database")

    def get_credential(self, key: str) -> Optional[str]:
        """Retrieve a credential.

        Args:
            key: Credential identifier

        Returns:
            Credential value or None if not found
        """
        if self._keyring_available:
            try:
                value = keyring.get_password(SERVICE_NAME, key)
                if value:
                    return value
            except Exception as e:
                logger.debug(f"Failed to retrieve from keyring: {e}")

        # Try fallback encrypted database storage
        if self.db:
            db_key = f"_secure_{key}"
            encrypted = self.db.get_config(db_key)
            if encrypted:
                try:
                    return self._decrypt(encrypted)
                except Exception as e:
                    logger.error(f"Failed to decrypt credential '{key}': {e}")
                    return None

        return None

    def delete_credential(self, key: str):
        """Delete a credential.

        Args:
            key: Credential identifier
        """
        if self._keyring_available:
            try:
                keyring.delete_password(SERVICE_NAME, key)
                logger.debug(f"Deleted credential '{key}' from keyring")
            except keyring.errors.PasswordDeleteError:
                pass  # Already deleted
            except Exception as e:
                logger.debug(f"Could not delete from keyring: {e}")

        # Also try to delete from database
        if self.db:
            db_key = f"_secure_{key}"
            try:
                self.db.set_config(db_key, None)
            except Exception:
                pass

    def migrate_plaintext_credential(self, key: str, plaintext_value: Optional[str]) -> bool:
        """Migrate a plaintext credential to secure storage.

        Args:
            key: Credential identifier
            plaintext_value: Current plaintext value

        Returns:
            True if migration was performed, False if no migration needed
        """
        if not plaintext_value:
            return False

        # Store in secure storage
        self.set_credential(key, plaintext_value)

        logger.info(f"Migrated credential '{key}' to secure storage")
        return True

    @property
    def is_keyring_available(self) -> bool:
        """Check if system keyring is being used.

        Returns:
            True if using system keyring, False if using encrypted fallback
        """
        return self._keyring_available

    def get_storage_info(self) -> str:
        """Get information about the storage backend in use.

        Returns:
            Human-readable description of storage backend
        """
        if self._keyring_available:
            backend = keyring.get_keyring()
            return f"System Keyring ({backend.__class__.__name__})"
        elif self.db:
            return "Encrypted Database (Fernet)"
        else:
            return "No secure storage available"
