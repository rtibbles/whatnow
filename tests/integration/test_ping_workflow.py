"""Integration tests for complete ping workflow."""

import pytest
import time
from unittest.mock import Mock, patch


class TestCompletePingWorkflow:
    """Integration tests for the complete ping workflow."""

    def test_work_session_with_pings(self, db, sample_local_todo):
        """Test complete workflow: start work, create TODO, record ping."""
        # Step 1: Start work session
        session_id = db.start_work_session()
        assert db.is_working()

        # Step 2: Create a local TODO
        todo_id = db.add_local_todo(**sample_local_todo)
        assert todo_id > 0

        # Step 3: Record a ping for this TODO
        timestamp = int(time.time())
        ping_id = db.add_ping(
            timestamp=timestamp,
            todo_id=str(todo_id),
            todo_type='local',
            tags=sample_local_todo['tags']
        )
        assert ping_id > 0

        # Step 4: Verify ping data
        pings = db.get_pings()
        assert len(pings) == 1
        ping = pings[0]
        assert ping['todo_id'] == str(todo_id)
        assert ping['todo_type'] == 'local'
        assert set(ping['tags']) == set(sample_local_todo['tags'])
        assert sample_local_todo['text'] in ping['activity']

        # Step 5: End work session
        time.sleep(0.1)
        db.end_work_session()
        assert not db.is_working()

        # Step 6: Verify work time tracking
        total_seconds = db.get_total_work_seconds_for_day(timestamp)
        assert total_seconds > 0

    def test_meeting_detection_and_logging(self, db, sample_calendar_event):
        """Test workflow: sync calendar, detect meeting, auto-log ping."""
        # Step 1: Sync calendar event
        db.upsert_calendar_event(sample_calendar_event)

        # Step 2: Check if there's a meeting at that time
        meeting_time = sample_calendar_event['start_time'] + 1800  # Middle of meeting
        event = db.get_event_at_time(meeting_time)
        assert event is not None
        assert event['summary'] == sample_calendar_event['summary']

        # Step 3: Auto-log ping for meeting
        ping_id = db.add_ping(
            timestamp=meeting_time,
            todo_id=event['id'],
            todo_type='meeting',
            tags=['meeting'],
            event_id=event['id'],
            is_meeting=True
        )

        # Step 4: Verify meeting ping
        pings = db.get_pings()
        assert len(pings) == 1
        ping = pings[0]
        assert ping['is_meeting']
        assert ping['todo_type'] == 'meeting'
        assert 'meeting' in ping['tags']
        assert sample_calendar_event['summary'] in ping['activity']

    def test_github_task_ping_workflow(self, db, sample_github_task):
        """Test workflow with GitHub task integration."""
        # Step 1: Sync GitHub task
        db.upsert_github_task(sample_github_task)

        tasks = db.get_github_tasks()
        assert len(tasks) == 1

        # Step 2: User selects GitHub task during ping
        timestamp = int(time.time())
        ping_id = db.add_ping(
            timestamp=timestamp,
            todo_id=sample_github_task['id'],
            todo_type='github',
            tags=sample_github_task['labels']
        )

        # Step 3: Verify ping with GitHub task
        pings = db.get_pings()
        assert len(pings) == 1
        ping = pings[0]
        assert ping['todo_id'] == sample_github_task['id']
        assert ping['todo_type'] == 'github'
        assert sample_github_task['title'] in ping['activity']

    def test_multiple_pings_time_analysis(self, db, sample_local_todo):
        """Test time analysis over multiple pings."""
        # Create multiple TODOs
        todo1_id = db.add_local_todo(
            text='Task 1',
            tags=['coding', 'python'],
            is_active=True,
            created_at=int(time.time())
        )

        todo2_id = db.add_local_todo(
            text='Task 2',
            tags=['meeting', 'planning'],
            is_active=True,
            created_at=int(time.time())
        )

        # Start work session
        db.start_work_session()

        # Record multiple pings over time
        base_timestamp = int(time.time())

        # 6 pings for Task 1
        for i in range(6):
            db.add_ping(
                timestamp=base_timestamp + i * 100,
                todo_id=str(todo1_id),
                todo_type='local',
                tags=['coding', 'python']
            )

        # 4 pings for Task 2
        for i in range(4):
            db.add_ping(
                timestamp=base_timestamp + (i + 6) * 100,
                todo_id=str(todo2_id),
                todo_type='local',
                tags=['meeting', 'planning']
            )

        # End work session
        time.sleep(0.1)
        db.end_work_session()

        # Analyze time distribution
        total_hours = db.get_total_work_seconds_for_day(base_timestamp) / 3600
        pings = db.get_pings_by_date_range(
            start_time=base_timestamp,
            end_time=base_timestamp + 1000
        )

        total_pings = len(pings)
        assert total_pings == 10

        # Count pings by TODO
        task1_pings = sum(1 for p in pings if p['todo_id'] == str(todo1_id))
        task2_pings = sum(1 for p in pings if p['todo_id'] == str(todo2_id))

        assert task1_pings == 6
        assert task2_pings == 4

        # Calculate time estimates (TagTime formula)
        task1_hours = (task1_pings / total_pings) * total_hours
        task2_hours = (task2_pings / total_pings) * total_hours

        # Task 1 should be 60% of time
        assert task1_pings / total_pings == pytest.approx(0.6)
        # Task 2 should be 40% of time
        assert task2_pings / total_pings == pytest.approx(0.4)

    def test_dismissed_and_completed_workflow(self, db, sample_local_todo):
        """Test workflow with dismissed pings and completed TODOs."""
        # Create TODO
        todo_id = db.add_local_todo(**sample_local_todo)

        timestamp = int(time.time())

        # Record some pings for the TODO
        for i in range(3):
            db.add_ping(
                timestamp=timestamp + i * 100,
                todo_id=str(todo_id),
                todo_type='local'
            )

        # Record a dismissed ping
        db.add_ping(
            timestamp=timestamp + 300,
            todo_id=None  # Dismissed
        )

        # Complete the TODO
        db.complete_local_todo(todo_id)

        # Verify TODO is completed
        active_todos = db.get_local_todos(active_only=True)
        assert len(active_todos) == 0

        # Verify all pings are recorded
        pings = db.get_pings()
        assert len(pings) == 4

        # Verify dismissed ping shows correctly
        dismissed_pings = [p for p in pings if p['todo_id'] is None]
        assert len(dismissed_pings) == 1
        assert "(Ping dismissed)" in dismissed_pings[0]['activity']


class TestCredentialIntegration:
    """Integration tests for credential storage in workflow."""

    def test_github_token_workflow(self, db, mock_keyring):
        """Test complete GitHub token storage and usage workflow."""
        # Step 1: User enters token in settings
        token = "ghp_test_token_abc123"
        db.set_github_token(token)

        # Step 2: App retrieves token for sync
        retrieved_token = db.get_github_token()
        assert retrieved_token == token

        # Step 3: Token is stored securely (not in plain config)
        config_value = db.get_config('github_token')
        assert config_value != token  # Should be migration marker

        # Step 4: User can delete token
        db.delete_github_token()
        assert db.get_github_token() is None

    def test_credential_migration_workflow(self, db, mock_keyring):
        """Test automatic migration of plaintext credentials."""
        # Step 1: Simulate old version with plaintext token
        plaintext_token = "ghp_old_plaintext_token"
        db.set_config('github_token', plaintext_token)

        # Step 2: Create new database instance (triggers migration)
        db2 = db.__class__(db_path=db.db_path)

        # Step 3: Token should be migrated to secure storage
        retrieved = db2.get_github_token()
        assert retrieved == plaintext_token

        # Step 4: Config should be marked as migrated
        config_value = db2.get_config('github_token')
        assert config_value == '_migrated_to_secure_storage'

        db2.close()


class TestSyncWorkflow:
    """Integration tests for sync workflows."""

    def test_github_sync_to_ping_workflow(self, db, sample_github_task):
        """Test full workflow from GitHub sync to ping recording."""
        # Step 1: Simulate GitHub sync
        tasks_to_sync = [sample_github_task]

        for task in tasks_to_sync:
            db.upsert_github_task(task)

        # Step 2: User sees tasks in UI
        tasks = db.get_github_tasks()
        assert len(tasks) == 1

        # Step 3: Ping triggers, user selects GitHub task
        timestamp = int(time.time())
        db.add_ping(
            timestamp=timestamp,
            todo_id=tasks[0]['id'],
            todo_type='github',
            tags=tasks[0]['labels']
        )

        # Step 4: Ping is recorded with task reference
        pings = db.get_pings()
        assert len(pings) == 1
        assert pings[0]['todo_type'] == 'github'
        assert sample_github_task['title'] in pings[0]['activity']

    def test_calendar_sync_meeting_detection(self, db, sample_calendar_event):
        """Test full workflow from calendar sync to meeting detection."""
        # Step 1: Simulate calendar sync
        events_to_sync = [sample_calendar_event]

        for event in events_to_sync:
            db.upsert_calendar_event(event)

        # Step 2: Ping triggers during meeting
        meeting_time = sample_calendar_event['start_time'] + 900  # 15 min into meeting

        # Step 3: App detects meeting
        event = db.get_event_at_time(meeting_time)
        assert event is not None

        # Step 4: App auto-logs ping (silently)
        db.add_ping(
            timestamp=meeting_time,
            todo_id=event['id'],
            todo_type='meeting',
            tags=['meeting'],
            event_id=event['id'],
            is_meeting=True
        )

        # Step 5: Meeting ping is recorded
        pings = db.get_pings()
        assert len(pings) == 1
        assert pings[0]['is_meeting']
        assert sample_calendar_event['summary'] in pings[0]['activity']

    def test_sync_metadata_tracking(self, db):
        """Test sync metadata tracking across syncs."""
        # Step 1: Initial sync
        db.update_sync_metadata(
            'github',
            success=True,
            sync_token='token_v1'
        )

        metadata = db.get_sync_metadata('github')
        assert metadata is not None
        assert metadata['sync_token'] == 'token_v1'
        assert metadata['last_success'] is not None

        # Step 2: Failed sync
        time.sleep(0.1)
        db.update_sync_metadata(
            'github',
            success=False,
            error_message='API rate limit'
        )

        metadata = db.get_sync_metadata('github')
        assert not metadata['error_message'] is None
        assert 'rate limit' in metadata['error_message'].lower()

        # Step 3: Successful sync updates
        time.sleep(0.1)
        db.update_sync_metadata(
            'github',
            success=True,
            sync_token='token_v2'
        )

        metadata = db.get_sync_metadata('github')
        assert metadata['sync_token'] == 'token_v2'
        assert metadata['error_message'] == ''  # Cleared on success


class TestEndToEndScenarios:
    """End-to-end scenario tests."""

    def test_typical_workday_scenario(self, db):
        """Test a typical workday scenario."""
        base_time = int(time.time())

        # Morning: Start work
        db.start_work_session()

        # Create today's TODOs
        todo1 = db.add_local_todo(
            text='Review PRs',
            tags=['code-review', 'github'],
            is_active=True,
            created_at=base_time
        )

        todo2 = db.add_local_todo(
            text='Write tests',
            tags=['testing', 'python'],
            is_active=True,
            created_at=base_time
        )

        # Record pings throughout the day
        current_time = base_time

        # Morning work on TODO 1
        for i in range(4):
            db.add_ping(
                timestamp=current_time,
                todo_id=str(todo1),
                todo_type='local',
                tags=['code-review']
            )
            current_time += 2700  # 45 min later

        # Mid-day meeting (simulated calendar event)
        meeting_event = {
            'id': 'meeting_123',
            'summary': 'Team standup',
            'description': 'Daily sync',
            'start_time': current_time,
            'end_time': current_time + 1800,  # 30 min
            'location': 'Conference Room',
            'calendar_id': 'primary',
            'attendees': ['team@example.com'],
            'url': 'https://calendar.google.com/event/123'
        }
        db.upsert_calendar_event(meeting_event)

        db.add_ping(
            timestamp=current_time + 900,
            todo_id=meeting_event['id'],
            todo_type='meeting',
            tags=['meeting'],
            event_id=meeting_event['id'],
            is_meeting=True
        )
        current_time += 1800

        # Afternoon work on TODO 2
        for i in range(5):
            db.add_ping(
                timestamp=current_time,
                todo_id=str(todo2),
                todo_type='local',
                tags=['testing']
            )
            current_time += 2700

        # End of day
        db.end_work_session()

        # Analyze the day
        pings = db.get_pings_by_date_range(base_time, current_time)
        total_pings = len(pings)
        assert total_pings == 10  # 4 + 1 + 5

        # Calculate time distribution
        work_seconds = db.get_total_work_seconds_for_day(base_time)
        work_hours = work_seconds / 3600

        todo1_pings = sum(1 for p in pings if p['todo_id'] == str(todo1))
        todo2_pings = sum(1 for p in pings if p['todo_id'] == str(todo2))
        meeting_pings = sum(1 for p in pings if p['is_meeting'])

        # Verify distribution
        assert todo1_pings == 4  # 40% of time
        assert todo2_pings == 5  # 50% of time
        assert meeting_pings == 1  # 10% of time

        # Calculate estimated hours
        todo1_hours = (todo1_pings / total_pings) * work_hours
        todo2_hours = (todo2_pings / total_pings) * work_hours
        meeting_hours = (meeting_pings / total_pings) * work_hours

        # Verify reasonable distribution
        assert todo1_hours > 0
        assert todo2_hours > todo1_hours  # Spent more time on TODO 2
        assert meeting_hours < todo1_hours  # Shortest time in meeting

        # Verify TODOs can be completed
        db.complete_local_todo(todo1)
        db.complete_local_todo(todo2)

        active_todos = db.get_local_todos(active_only=True)
        assert len(active_todos) == 0
