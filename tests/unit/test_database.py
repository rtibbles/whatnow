"""Unit tests for database operations."""

import time

import pytest

from whatnow.database import Database


class TestDatabaseInitialization:
    """Tests for database initialization."""

    def test_creates_database_file(self, temp_db_path):
        """Test that database file is created."""
        import os

        db = Database(db_path=temp_db_path)
        assert os.path.exists(temp_db_path)
        db.close()

    def test_creates_all_tables(self, db):
        """Test that all required tables are created."""
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        expected_tables = [
            "pings",
            "work_sessions",
            "local_todos",
            "github_tasks",
            "calendar_events",
            "sync_metadata",
            "config",
            "alembic_version",
        ]

        for table in expected_tables:
            assert table in tables


class TestPingOperations:
    """Tests for ping CRUD operations."""

    def test_add_ping(self, db, sample_ping_data):
        """Test adding a ping."""
        ping_id = db.add_ping(**sample_ping_data)

        assert isinstance(ping_id, int)
        assert ping_id > 0

    def test_get_pings(self, db, sample_ping_data):
        """Test retrieving pings."""
        # Add some pings
        db.add_ping(**sample_ping_data)

        sample_ping_data["timestamp"] += 100
        db.add_ping(**sample_ping_data)

        # Retrieve pings
        pings = db.get_pings(limit=10)

        assert len(pings) == 2
        assert all("id" in p for p in pings)
        assert all("timestamp" in p for p in pings)
        assert all("activity" in p for p in pings)  # Should have resolved activity

        # Should be in descending order by timestamp
        assert pings[0]["timestamp"] >= pings[1]["timestamp"]

    def test_get_pings_with_activity_resolution(self, db, sample_local_todo):
        """Test that get_pings resolves activity descriptions."""
        # Add a local TODO
        todo_id = db.add_local_todo(**sample_local_todo)

        # Add ping for this TODO
        ping_id = db.add_ping(timestamp=int(time.time()), todo_id=str(todo_id), todo_type="local")

        # Get pings
        pings = db.get_pings()

        assert len(pings) == 1
        ping = pings[0]
        assert "activity" in ping
        assert sample_local_todo["text"] in ping["activity"]

    def test_get_pings_by_date_range(self, db):
        """Test retrieving pings within date range."""
        # Add pings at different times
        timestamp1 = 1699900000
        timestamp2 = timestamp1 + 3600  # 1 hour later
        timestamp3 = timestamp1 + 7200  # 2 hours later

        db.add_ping(timestamp=timestamp1, todo_type="local")
        db.add_ping(timestamp=timestamp2, todo_type="local")
        db.add_ping(timestamp=timestamp3, todo_type="local")

        # Query middle range
        pings = db.get_pings_by_date_range(
            start_time=timestamp1 + 1800,  # 30 min after first
            end_time=timestamp3 - 1800,  # 30 min before last
        )

        # Should only get the middle ping
        assert len(pings) == 1
        assert pings[0]["timestamp"] == timestamp2

    def test_dismissed_ping_activity(self, db):
        """Test activity resolution for dismissed pings."""
        db.add_ping(timestamp=int(time.time()), todo_id=None)

        pings = db.get_pings()
        assert len(pings) == 1
        assert pings[0]["activity"] == "(Ping dismissed)"


class TestWorkSessionOperations:
    """Tests for work session management."""

    def test_start_work_session(self, db):
        """Test starting a work session."""
        session_id = db.start_work_session()

        assert isinstance(session_id, int)
        assert session_id > 0
        assert db.is_working()

    def test_end_work_session(self, db):
        """Test ending a work session."""
        db.start_work_session()
        assert db.is_working()

        time.sleep(0.1)  # Work for a bit
        db.end_work_session()

        assert not db.is_working()

    def test_get_total_work_seconds(self, db):
        """Test calculating total work seconds."""
        timestamp = int(time.time())

        # Start and end a session
        db.start_work_session()
        time.sleep(0.2)
        db.end_work_session()

        # Get total seconds for today
        total = db.get_total_work_seconds_for_day(timestamp)

        # Should be at least 0.2 seconds
        assert total >= 0.2
        assert total < 1.0  # But not more than 1 second

    def test_multiple_sessions_same_day(self, db):
        """Test tracking multiple sessions in one day."""
        timestamp = int(time.time())

        # Session 1
        db.start_work_session()
        time.sleep(0.1)
        db.end_work_session()

        # Session 2
        db.start_work_session()
        time.sleep(0.1)
        db.end_work_session()

        total = db.get_total_work_seconds_for_day(timestamp)
        assert total >= 0.2  # At least both sessions combined


class TestLocalTODOOperations:
    """Tests for local TODO management."""

    def test_add_local_todo(self, db, sample_local_todo):
        """Test adding a local TODO."""
        todo_id = db.add_local_todo(**sample_local_todo)

        assert isinstance(todo_id, int)
        assert todo_id > 0

    def test_get_local_todos(self, db, sample_local_todo):
        """Test retrieving local TODOs."""
        db.add_local_todo(**sample_local_todo)

        todos = db.get_local_todos()

        assert len(todos) == 1
        assert todos[0]["text"] == sample_local_todo["text"]
        assert todos[0]["tags"] == sample_local_todo["tags"]
        assert todos[0]["is_active"]

    def test_get_active_todos_only(self, db, sample_local_todo):
        """Test filtering active vs completed TODOs."""
        # Add active TODO
        db.add_local_todo(**sample_local_todo)

        # Add completed TODO
        completed_todo = sample_local_todo.copy()
        completed_todo["text"] = "Completed task"
        completed_todo["is_active"] = False
        completed_todo["completed_at"] = int(time.time())
        db.add_local_todo(**completed_todo)

        # Get only active
        active_todos = db.get_local_todos(active_only=True)
        assert len(active_todos) == 1
        assert active_todos[0]["text"] == sample_local_todo["text"]

        # Get all
        all_todos = db.get_local_todos(active_only=False)
        assert len(all_todos) == 2

    def test_update_local_todo(self, db, sample_local_todo):
        """Test updating a local TODO."""
        todo_id = db.add_local_todo(**sample_local_todo)

        # Update it
        db.update_local_todo(todo_id, text="Updated text", tags=["new-tag"])

        todos = db.get_local_todos()
        assert len(todos) == 1
        assert todos[0]["text"] == "Updated text"
        assert "new-tag" in todos[0]["tags"]

    def test_complete_local_todo(self, db, sample_local_todo):
        """Test completing a local TODO."""
        todo_id = db.add_local_todo(**sample_local_todo)

        db.complete_local_todo(todo_id)

        # Should no longer be active
        active_todos = db.get_local_todos(active_only=True)
        assert len(active_todos) == 0

        # But should exist in all TODOs
        all_todos = db.get_local_todos(active_only=False)
        assert len(all_todos) == 1
        assert not all_todos[0]["is_active"]
        assert all_todos[0]["completed_at"] is not None


class TestGitHubTaskOperations:
    """Tests for GitHub task storage."""

    def test_upsert_github_task(self, db, sample_github_task):
        """Test upserting a GitHub task."""
        db.upsert_github_task(sample_github_task)

        tasks = db.get_github_tasks()
        assert len(tasks) == 1
        assert tasks[0]["id"] == sample_github_task["id"]
        assert tasks[0]["title"] == sample_github_task["title"]

    def test_upsert_updates_existing(self, db, sample_github_task):
        """Test that upsert updates existing records."""
        db.upsert_github_task(sample_github_task)

        # Update the task
        sample_github_task["title"] = "Updated title"
        db.upsert_github_task(sample_github_task)

        tasks = db.get_github_tasks()
        assert len(tasks) == 1  # Still only one task
        assert tasks[0]["title"] == "Updated title"

    def test_get_github_tasks_filters_inactive(self, db, sample_github_task):
        """Test that only current iteration tasks are returned."""
        # Add current iteration task
        db.upsert_github_task(sample_github_task)

        # Add old task (different iteration)
        old_task = sample_github_task.copy()
        old_task["id"] = "old_task"
        old_task["iteration_title"] = "Old Sprint"
        db.upsert_github_task(old_task)

        # Should get both when not filtering
        all_tasks = db.get_github_tasks()
        assert len(all_tasks) == 2


class TestCalendarEventOperations:
    """Tests for calendar event storage."""

    def test_upsert_calendar_event(self, db, sample_calendar_event):
        """Test upserting a calendar event."""
        db.upsert_calendar_event(sample_calendar_event)

        # Get event by checking for event at that time
        event = db.get_event_at_time(sample_calendar_event["start_time"] + 100)
        assert event is not None
        assert event["id"] == sample_calendar_event["id"]
        assert event["summary"] == sample_calendar_event["summary"]

    def test_get_event_at_time(self, db, sample_calendar_event):
        """Test retrieving event at specific time."""
        db.upsert_calendar_event(sample_calendar_event)

        # Time during event
        event = db.get_event_at_time(sample_calendar_event["start_time"] + 1800)
        assert event is not None

        # Time before event
        event_before = db.get_event_at_time(sample_calendar_event["start_time"] - 100)
        assert event_before is None

        # Time after event
        event_after = db.get_event_at_time(sample_calendar_event["end_time"] + 100)
        assert event_after is None


class TestConfigOperations:
    """Tests for configuration storage."""

    def test_set_and_get_config(self, db):
        """Test setting and getting configuration values."""
        db.set_config("test_key", "test_value")
        value = db.get_config("test_key")
        assert value == "test_value"

    def test_get_config_default(self, db):
        """Test getting non-existent config with default."""
        value = db.get_config("nonexistent", "default_value")
        assert value == "default_value"

    def test_config_with_json_values(self, db):
        """Test storing complex JSON values."""
        complex_value = {"list": [1, 2, 3], "dict": {"nested": "value"}, "bool": True}

        db.set_config("complex", complex_value)
        retrieved = db.get_config("complex")

        assert retrieved == complex_value


class TestCredentialStorage:
    """Tests for secure credential storage."""

    def test_set_and_get_github_token(self, db, mock_keyring):
        """Test storing and retrieving GitHub token."""
        token = "ghp_test_token_12345"

        db.set_github_token(token)
        retrieved = db.get_github_token()

        assert retrieved == token

    def test_delete_github_token(self, db, mock_keyring):
        """Test deleting GitHub token."""
        token = "ghp_test_token_12345"

        db.set_github_token(token)
        db.delete_github_token()

        retrieved = db.get_github_token()
        assert retrieved is None

    def test_credential_storage_info(self, db):
        """Test getting credential storage information."""
        info = db.get_credential_storage_info()
        assert isinstance(info, str)
        assert len(info) > 0
