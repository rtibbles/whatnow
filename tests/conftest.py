"""Pytest configuration and fixtures for WhatNow tests."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path.

    Yields:
        Path to temporary database file
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def db(temp_db_path):
    """Create a test database instance.

    Returns:
        Database instance with temporary file
    """
    from whatnow.database import Database

    db = Database(db_path=temp_db_path)
    yield db

    # Cleanup
    db.close()


@pytest.fixture
def mock_keyring(monkeypatch):
    """Mock keyring for credential storage tests.

    Returns:
        Mock keyring module
    """
    mock_keyring = MagicMock()
    mock_storage = {}

    def get_password(service, key):
        return mock_storage.get(f"{service}:{key}")

    def set_password(service, key, value):
        mock_storage[f"{service}:{key}"] = value

    def delete_password(service, key):
        mock_storage.pop(f"{service}:{key}", None)

    mock_keyring.get_password = Mock(side_effect=get_password)
    mock_keyring.set_password = Mock(side_effect=set_password)
    mock_keyring.delete_password = Mock(side_effect=delete_password)

    # Create a mock backend with a name
    mock_backend = Mock()
    mock_backend.__class__.__name__ = "MockBackend"
    mock_keyring.get_keyring = Mock(return_value=mock_backend)

    monkeypatch.setattr("keyring.get_password", mock_keyring.get_password)
    monkeypatch.setattr("keyring.set_password", mock_keyring.set_password)
    monkeypatch.setattr("keyring.delete_password", mock_keyring.delete_password)
    monkeypatch.setattr("keyring.get_keyring", mock_keyring.get_keyring)

    return mock_keyring


@pytest.fixture
def sample_ping_data():
    """Sample ping data for testing.

    Returns:
        Dictionary with sample ping data
    """
    return {
        "timestamp": 1699900000,
        "todo_id": "test-todo-1",
        "todo_type": "local",
        "tags": ["work", "coding"],
        "notes": "Working on tests",
        "is_meeting": False,
    }


@pytest.fixture
def sample_github_task():
    """Sample GitHub task data for testing.

    Returns:
        Dictionary with sample GitHub task data
    """
    return {
        "id": "PVTI_test123",
        "title": "Implement feature X",
        "body": "Description of feature X",
        "state": "TODO",
        "labels": ["enhancement", "priority-high"],
        "assignees": ["developer1"],
        "url": "https://github.com/org/repo/issues/123",
        "created_at": 1699800000,
        "updated_at": 1699900000,
        "iteration_title": "Sprint 1",
    }


@pytest.fixture
def sample_calendar_event():
    """Sample calendar event data for testing.

    Returns:
        Dictionary with sample calendar event data
    """
    return {
        "id": "event_test123",
        "summary": "Team meeting",
        "description": "Weekly sync",
        "start_time": 1699900000,
        "end_time": 1699903600,  # 1 hour later
        "location": "Conference Room A",
        "calendar_id": "primary",
        "attendees": ["user1@example.com", "user2@example.com"],
        "url": "https://calendar.google.com/event/123",
    }


@pytest.fixture
def sample_local_todo():
    """Sample local TODO data for testing.

    Returns:
        Dictionary with sample local TODO data
    """
    return {
        "text": "Fix bug in authentication",
        "tags": ["bug", "priority-high"],
        "created_at": 1699800000,
    }


@pytest.fixture
def mock_github_api(mocker):
    """Mock GitHub GraphQL API responses.

    Returns:
        Mock requests object
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {"organization": {"projectV2": {"items": {"nodes": []}}}}
    }

    mock_post = mocker.patch("requests.post", return_value=mock_response)
    return mock_post


@pytest.fixture
def mock_gcal_api(mocker):
    """Mock Google Calendar API responses.

    Returns:
        Mock Google Calendar service
    """
    mock_service = Mock()
    mock_events = Mock()
    mock_events.list.return_value.execute.return_value = {
        "items": [],
        "nextSyncToken": "test_sync_token",
    }
    mock_service.events.return_value = mock_events

    return mock_service


@pytest.fixture
def poisson_intervals():
    """Fixture to set deterministic random seed for Poisson distribution tests.

    Yields:
        None, but sets random seed
    """
    import random

    old_state = random.getstate()
    random.seed(42)  # Deterministic randomness for testing

    yield

    random.setstate(old_state)


@pytest.fixture(scope="session")
def gtk_display():
    """Check if GTK display is available.

    Yields:
        True if display available, False otherwise
    """
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        # Try to initialize
        Gtk.init_check(None)
        yield True
    except Exception:
        yield False


# Markers for conditional test skipping
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "requires_gtk: mark test as requiring GTK display")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Skip tests that require GTK if display not available."""
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        Gtk.init_check(None)
        gtk_available = True
    except Exception:
        gtk_available = False

    if not gtk_available:
        skip_gtk = pytest.mark.skip(reason="GTK display not available")
        for item in items:
            if "requires_gtk" in item.keywords:
                item.add_marker(skip_gtk)
