"""Unit tests for credential storage."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from whatnow.credentials import CredentialStore


class TestCredentialStore:
    """Tests for CredentialStore class."""

    def test_initialization_with_keyring(self, db, mock_keyring):
        """Test initialization when keyring is available."""
        store = CredentialStore(db=db)

        assert store.db == db
        assert store.is_keyring_available

    def test_initialization_without_keyring(self, db, monkeypatch):
        """Test initialization when keyring is not available."""

        # Mock keyring to fail
        def mock_get_keyring():
            return None

        monkeypatch.setattr("keyring.get_keyring", mock_get_keyring)

        store = CredentialStore(db=db)

        assert not store.is_keyring_available
        assert store._encryption_key is not None  # Should have fallback encryption

    def test_set_and_get_credential_with_keyring(self, db, mock_keyring):
        """Test storing and retrieving credentials with keyring."""
        store = CredentialStore(db=db)

        store.set_credential("test_key", "test_value")
        retrieved = store.get_credential("test_key")

        assert retrieved == "test_value"
        # Verify keyring was used
        assert mock_keyring.set_password.called
        assert mock_keyring.get_password.called

    def test_set_empty_credential_deletes(self, db, mock_keyring):
        """Test that setting empty value deletes the credential."""
        store = CredentialStore(db=db)

        store.set_credential("test_key", "test_value")
        store.set_credential("test_key", "")  # Empty value

        retrieved = store.get_credential("test_key")
        assert retrieved is None

    def test_delete_credential(self, db, mock_keyring):
        """Test deleting a credential."""
        store = CredentialStore(db=db)

        store.set_credential("test_key", "test_value")
        store.delete_credential("test_key")

        retrieved = store.get_credential("test_key")
        assert retrieved is None

    def test_encrypted_fallback_storage(self, db, monkeypatch):
        """Test encrypted fallback when keyring unavailable."""
        # Disable keyring
        monkeypatch.setattr("keyring.get_keyring", lambda: None)

        store = CredentialStore(db=db)
        assert not store.is_keyring_available

        # Store and retrieve credential
        store.set_credential("test_key", "test_value")
        retrieved = store.get_credential("test_key")

        assert retrieved == "test_value"

        # Verify it's encrypted in database
        encrypted = db.get_config("_secure_test_key")
        assert encrypted is not None
        assert encrypted != "test_value"  # Should be encrypted

    def test_encryption_consistency(self, db, monkeypatch):
        """Test that encrypted values can be decrypted consistently."""
        monkeypatch.setattr("keyring.get_keyring", lambda: None)

        store1 = CredentialStore(db=db)
        store1.set_credential("test", "secret")

        # Create new store instance with same database
        store2 = CredentialStore(db=db)
        retrieved = store2.get_credential("test")

        assert retrieved == "secret"

    def test_migrate_plaintext_credential(self, db, mock_keyring):
        """Test migrating plaintext credentials to secure storage."""
        store = CredentialStore(db=db)

        plaintext = "plaintext_token"
        migrated = store.migrate_plaintext_credential("github_token", plaintext)

        assert migrated is True

        # Should now be in secure storage
        retrieved = store.get_credential("github_token")
        assert retrieved == plaintext

    def test_migrate_empty_credential(self, db, mock_keyring):
        """Test that empty credentials are not migrated."""
        store = CredentialStore(db=db)

        migrated = store.migrate_plaintext_credential("test", None)
        assert migrated is False

        migrated = store.migrate_plaintext_credential("test", "")
        assert migrated is False

    def test_get_storage_info(self, db, mock_keyring):
        """Test getting storage backend information."""
        store = CredentialStore(db=db)
        info = store.get_storage_info()

        assert isinstance(info, str)
        assert len(info) > 0
        # Should mention either keyring or encryption
        assert "Keyring" in info or "Encrypted" in info

    def test_keyring_fallback_on_error(self, db, monkeypatch):
        """Test fallback to encrypted storage if keyring operations fail."""
        # Mock keyring to appear available but fail on operations
        mock_keyring = MagicMock()
        mock_backend = Mock()
        mock_backend.__class__.__name__ = "MockBackend"
        mock_keyring.get_keyring.return_value = mock_backend
        mock_keyring.set_password.side_effect = Exception("Keyring error")
        mock_keyring.get_password.side_effect = Exception("Keyring error")

        monkeypatch.setattr("keyring.get_keyring", mock_keyring.get_keyring)
        monkeypatch.setattr("keyring.set_password", mock_keyring.set_password)
        monkeypatch.setattr("keyring.get_password", mock_keyring.get_password)

        store = CredentialStore(db=db)

        # Should fall back to encrypted database storage
        store.set_credential("test", "value")
        retrieved = store.get_credential("test")

        # Should still work via encrypted fallback
        assert retrieved == "value"


class TestCredentialEncryption:
    """Tests for credential encryption functionality."""

    def test_encrypt_decrypt_roundtrip(self, db, monkeypatch):
        """Test that encrypted values can be decrypted."""
        monkeypatch.setattr("keyring.get_keyring", lambda: None)

        store = CredentialStore(db=db)

        test_values = [
            "simple",
            "with spaces",
            "with-special-!@#$%^&*()",
            "unicode: 你好世界",
            "a" * 1000,  # Long string
        ]

        for value in test_values:
            encrypted = store._encrypt(value)
            decrypted = store._decrypt(encrypted)
            assert decrypted == value

    def test_different_values_different_encryption(self, db, monkeypatch):
        """Test that different values produce different encryptions."""
        monkeypatch.setattr("keyring.get_keyring", lambda: None)

        store = CredentialStore(db=db)

        encrypted1 = store._encrypt("value1")
        encrypted2 = store._encrypt("value2")

        assert encrypted1 != encrypted2

    def test_encryption_key_persistence(self, db, monkeypatch):
        """Test that encryption key persists across instances."""
        monkeypatch.setattr("keyring.get_keyring", lambda: None)

        # First instance creates key and encrypts
        store1 = CredentialStore(db=db)
        encrypted = store1._encrypt("test")

        # Second instance should use same key
        store2 = CredentialStore(db=db)
        decrypted = store2._decrypt(encrypted)

        assert decrypted == "test"


class TestKeyringAvailability:
    """Tests for keyring availability detection."""

    def test_check_keyring_when_available(self, mock_keyring):
        """Test keyring detection when available."""
        # Mock is already set up by fixture
        from whatnow.credentials import CredentialStore

        # Create store without DB to just test keyring check
        store = CredentialStore.__new__(CredentialStore)
        available = store._check_keyring()

        assert available is True

    def test_check_keyring_when_unavailable(self, monkeypatch):
        """Test keyring detection when unavailable."""
        monkeypatch.setattr("keyring.get_keyring", lambda: None)

        from whatnow.credentials import CredentialStore

        store = CredentialStore.__new__(CredentialStore)
        available = store._check_keyring()

        assert available is False

    def test_check_keyring_when_backend_fails(self, monkeypatch):
        """Test keyring detection when backend operations fail."""

        def mock_set_password(*args):
            raise Exception("Backend not available")

        monkeypatch.setattr("keyring.set_password", mock_set_password)
        monkeypatch.setattr("keyring.get_keyring", lambda: Mock())

        from whatnow.credentials import CredentialStore

        store = CredentialStore.__new__(CredentialStore)
        available = store._check_keyring()

        assert available is False
