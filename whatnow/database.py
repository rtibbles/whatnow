"""Database management for WhatNow using SQLAlchemy.

This module provides the Database class, which is the main interface for all
database operations in WhatNow. It uses SQLAlchemy ORM with SQLite for local
storage and includes Alembic integration for schema migrations.

Key Responsibilities:
- Ping storage and retrieval with activity resolution
- GitHub task synchronization data
- Google Calendar event caching
- Local TODO management
- Work session tracking
- Sync metadata and status tracking
- Secure credential storage (via keyring integration)
- Database migrations via Alembic

Thread Safety:
The Database class uses scoped_session to ensure thread-local sessions,
making it safe to use from multiple threads (ping scheduler, sync threads,
UI thread).

Database Schema:
- pings: Activity ping records with timestamps and tags
- local_todos: User-created TODO items
- github_tasks: Synced tasks from GitHub Projects
- calendar_events: Synced events from Google Calendar
- work_sessions: Explicit work session start/stop tracking
- sync_metadata: Last sync times and status for external services
- config: Key-value configuration storage
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, create_engine, select
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from .models import (
    Base,
    CalendarEvent,
    Config,
    GitHubTask,
    LocalTODO,
    Ping,
    SyncMetadata,
    WorkSession,
)

logger = logging.getLogger(__name__)


class Database:
    """SQLAlchemy database manager for local-first storage."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Use XDG_DATA_HOME or default to ~/.local/share
            data_dir = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
            app_dir = Path(data_dir) / "whatnow"
            app_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(app_dir / "whatnow.db")

        self.db_path = db_path
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            # Enable thread-safe connection pooling for SQLite
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,  # Verify connections before use
        )
        # Use scoped_session for thread-local sessions
        session_factory = sessionmaker(bind=self.engine)
        self.SessionLocal = scoped_session(session_factory)

        # Create backups directory
        self.backup_dir = Path(self.db_path).parent / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Run database migrations
        self._run_migrations()

        # Initialize secure credential storage
        from .credentials import CredentialStore

        self._credentials = CredentialStore(db=self)

        # Migrate existing plaintext credentials
        self._migrate_plaintext_credentials()

    def _run_migrations(self):
        """Run Alembic migrations to upgrade database schema."""
        try:
            import shutil
            import tempfile

            from alembic import command
            from alembic.config import Config

            # Get the package directory where alembic.ini is located
            package_dir = Path(__file__).parent

            # Create Alembic config
            alembic_cfg = Config(str(package_dir / "alembic.ini"))

            # Set the script location to the absolute path of the alembic directory
            alembic_cfg.set_main_option("script_location", str(package_dir / "alembic"))

            # Set the database URL
            alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{self.db_path}")

            # Create backup before migrations if database exists and has data
            if Path(self.db_path).exists() and Path(self.db_path).stat().st_size > 0:
                logger.info("Creating backup before migrations...")
                self.create_backup(reason="pre_migration")

            # Run upgrade to head
            logger.info("Checking for database migrations...")
            command.upgrade(alembic_cfg, "head")

        except Exception as e:
            # If migrations fail, fall back to creating tables directly
            # This handles the case where Alembic isn't set up yet or there are issues
            logger.warning(f"Migration check failed: {e}, falling back to direct table creation")
            Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get a new database session.

        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()

    # Backup operations
    def create_backup(self, reason: str = "manual") -> Optional[str]:
        """Create a backup of the database.

        Args:
            reason: Reason for backup (e.g., 'manual', 'pre_migration', 'periodic')

        Returns:
            Path to backup file, or None if backup failed
        """
        try:
            import shutil
            from datetime import datetime

            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"whatnow_backup_{timestamp}_{reason}.db"
            backup_path = self.backup_dir / backup_filename

            # Close any open connections temporarily
            self.SessionLocal.remove()

            # Copy database file
            shutil.copy2(self.db_path, backup_path)

            logger.info(f"Database backup created: {backup_path}")

            # Clean up old backups (keep last 10)
            self._cleanup_old_backups(keep=10)

            return str(backup_path)

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def _cleanup_old_backups(self, keep: int = 10):
        """Clean up old backup files, keeping only the most recent ones.

        Args:
            keep: Number of backups to keep
        """
        try:
            # Get all backup files sorted by modification time
            backups = sorted(
                self.backup_dir.glob("whatnow_backup_*.db"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            # Remove old backups
            for backup in backups[keep:]:
                backup.unlink()
                logger.info(f"Removed old backup: {backup}")

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")

    def export_data(self, export_path: str) -> bool:
        """Export all data to a JSON file.

        Args:
            export_path: Path to export file

        Returns:
            True if export successful, False otherwise
        """
        try:
            import json
            from datetime import datetime

            # Gather all data
            data = {
                "export_date": datetime.now().isoformat(),
                "pings": self.get_pings(limit=100000),  # Export all pings
                "local_todos": self.get_local_todos(active_only=False),
                "github_tasks": self.get_github_tasks(),
                "work_sessions": self._export_work_sessions(),
                "config": self._export_config(),
            }

            # Write to file
            with open(export_path, "w") as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Data exported to: {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return False

    def _export_work_sessions(self) -> List[Dict[str, Any]]:
        """Export work sessions for data export.

        Returns:
            List of work session dictionaries
        """
        with self.get_session() as session:
            sessions = session.execute(select(WorkSession)).scalars().all()
            return [
                {
                    "id": s.id,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                }
                for s in sessions
            ]

    def _export_config(self) -> Dict[str, Any]:
        """Export configuration for data export.

        Returns:
            Dictionary of configuration values
        """
        with self.get_session() as session:
            configs = session.execute(select(Config)).scalars().all()
            return {c.key: c.value for c in configs}

    # Ping operations
    def add_ping(
        self,
        timestamp: int,
        todo_id: Optional[str] = None,
        todo_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
        event_id: Optional[str] = None,
        is_meeting: bool = False,
    ) -> int:
        """Add a new ping to the database.

        Args:
            timestamp: Unix timestamp of the ping
            todo_id: ID of associated TODO (GitHub task ID or local TODO ID)
            todo_type: Type of TODO ('github', 'local', 'meeting')
            tags: Optional list of tags
            notes: Optional additional notes
            event_id: Calendar event ID if this is a meeting ping
            is_meeting: Whether this ping is for a meeting

        Returns:
            ID of the inserted ping
        """
        with self.get_session() as session:
            ping = Ping(
                timestamp=timestamp,
                todo_id=todo_id,
                todo_type=todo_type,
                tags=tags,
                notes=notes,
                event_id=event_id,
                is_meeting=is_meeting,
            )
            session.add(ping)
            session.commit()
            session.refresh(ping)
            return int(ping.id)

    def get_pings(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get recent pings.

        Args:
            limit: Maximum number of pings to return
            offset: Number of pings to skip

        Returns:
            List of ping dictionaries with activity descriptions
        """
        with self.get_session() as session:
            stmt = select(Ping).order_by(Ping.timestamp.desc()).limit(limit).offset(offset)
            pings = session.execute(stmt).scalars().all()

            result = []
            for p in pings:
                # Resolve activity description
                activity = self._resolve_ping_activity(p, session)

                result.append(
                    {
                        "id": p.id,
                        "timestamp": p.timestamp,
                        "todo_id": p.todo_id,
                        "todo_type": p.todo_type,
                        "tags": p.tags or [],
                        "notes": p.notes,
                        "event_id": p.event_id,
                        "is_meeting": p.is_meeting,
                        "created_at": p.created_at,
                        "activity": activity,
                    }
                )

            return result

    def count_pings(self) -> int:
        """Get total count of pings in database.

        Returns:
            Total number of pings
        """
        with self.get_session() as session:
            from sqlalchemy import func

            stmt = select(func.count(Ping.id))
            count = session.execute(stmt).scalar()
            return count or 0

    def get_pings_by_date_range(self, start_time: int, end_time: int) -> List[Dict[str, Any]]:
        """Get pings within a date range.

        Args:
            start_time: Start timestamp (inclusive)
            end_time: End timestamp (inclusive)

        Returns:
            List of ping dictionaries with activity descriptions
        """
        with self.get_session() as session:
            stmt = (
                select(Ping)
                .where(and_(Ping.timestamp >= start_time, Ping.timestamp <= end_time))
                .order_by(Ping.timestamp.desc())
            )
            pings = session.execute(stmt).scalars().all()

            result = []
            for p in pings:
                # Resolve activity description
                activity = self._resolve_ping_activity(p, session)

                result.append(
                    {
                        "id": p.id,
                        "timestamp": p.timestamp,
                        "todo_id": p.todo_id,
                        "todo_type": p.todo_type,
                        "tags": p.tags or [],
                        "notes": p.notes,
                        "event_id": p.event_id,
                        "is_meeting": p.is_meeting,
                        "created_at": p.created_at,
                        "activity": activity,
                    }
                )

            return result

    # Work session operations
    def start_work_session(self) -> int:
        """Start a new work session.

        Returns:
            ID of the work session
        """
        with self.get_session() as session:
            now = int(datetime.now().timestamp())
            work_session = WorkSession(start_time=now)
            session.add(work_session)
            session.commit()
            session.refresh(work_session)
            return int(work_session.id)

    def end_work_session(self) -> Optional[int]:
        """End the current work session.

        Returns:
            Total seconds worked, or None if no active session
        """
        with self.get_session() as session:
            # Find active work session (no end_time)
            stmt = (
                select(WorkSession)
                .where(WorkSession.end_time == None)
                .order_by(WorkSession.start_time.desc())
            )
            result = session.execute(stmt).scalars().first()

            if result:
                now = int(datetime.now().timestamp())
                result.end_time = now
                result.total_seconds = now - result.start_time
                session.commit()
                return int(result.total_seconds) if result.total_seconds is not None else None

            return None

    def get_current_work_session(self) -> Optional[Dict[str, Any]]:
        """Get the current active work session.

        Returns:
            Work session dictionary or None if not working
        """
        with self.get_session() as session:
            stmt = (
                select(WorkSession)
                .where(WorkSession.end_time == None)
                .order_by(WorkSession.start_time.desc())
            )
            result = session.execute(stmt).scalars().first()

            if result:
                return {
                    "id": result.id,
                    "start_time": result.start_time,
                    "end_time": result.end_time,
                    "total_seconds": result.total_seconds,
                }

            return None

    def is_working(self) -> bool:
        """Check if currently in a work session.

        Returns:
            True if working, False otherwise
        """
        return self.get_current_work_session() is not None

    def toggle_work_session(self) -> tuple[bool, Optional[int]]:
        """Atomically toggle work session state.

        This method safely handles the check-then-act pattern within a single
        database transaction, preventing race conditions.

        Returns:
            Tuple of (is_now_working, session_id_or_seconds)
            - If starting work: (True, session_id)
            - If ending work: (False, total_seconds)
        """
        with self.get_session() as session:
            # Find active work session within the transaction
            stmt = (
                select(WorkSession)
                .where(WorkSession.end_time == None)
                .order_by(WorkSession.start_time.desc())
            )
            active_session = session.execute(stmt).scalars().first()

            now = int(datetime.now().timestamp())

            if active_session:
                # End the active session
                active_session.end_time = now
                active_session.total_seconds = now - active_session.start_time
                session.commit()
                return (False, active_session.total_seconds)
            else:
                # Start a new session
                work_session = WorkSession(start_time=now)
                session.add(work_session)
                session.commit()
                session.refresh(work_session)
                return (True, work_session.id)

    def get_work_sessions_by_date(self, date_timestamp: int) -> List[Dict[str, Any]]:
        """Get work sessions for a specific day.

        Args:
            date_timestamp: Unix timestamp within the desired day

        Returns:
            List of work session dictionaries
        """
        # Get start and end of day
        dt = datetime.fromtimestamp(date_timestamp)
        day_start = datetime(dt.year, dt.month, dt.day, 0, 0, 0)
        day_end = datetime(dt.year, dt.month, dt.day, 23, 59, 59)

        start_ts = int(day_start.timestamp())
        end_ts = int(day_end.timestamp())

        with self.get_session() as session:
            stmt = (
                select(WorkSession)
                .where(and_(WorkSession.start_time >= start_ts, WorkSession.start_time <= end_ts))
                .order_by(WorkSession.start_time)
            )
            sessions = session.execute(stmt).scalars().all()

            return [
                {
                    "id": s.id,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "total_seconds": s.total_seconds,
                }
                for s in sessions
            ]

    def get_total_work_seconds_for_day(self, date_timestamp: int) -> int:
        """Get total seconds worked on a specific day.

        Args:
            date_timestamp: Unix timestamp within the desired day

        Returns:
            Total seconds worked
        """
        sessions = self.get_work_sessions_by_date(date_timestamp)
        total: int = sum(
            s.get("total_seconds", 0) for s in sessions if s.get("total_seconds") is not None
        )

        # Add current session if active and started today
        current = self.get_current_work_session()
        if current:
            dt = datetime.fromtimestamp(date_timestamp)
            current_dt = datetime.fromtimestamp(current["start_time"])
            if current_dt.date() == dt.date():
                now = int(datetime.now().timestamp())
                total += now - current["start_time"]

        return int(total)

    # Local TODO operations
    def add_local_todo(
        self,
        text: str,
        tags: Optional[List[str]] = None,
        is_active: bool = True,
        created_at: Optional[int] = None,
        completed_at: Optional[int] = None,
    ) -> int:
        """Add a new local TODO.

        Args:
            text: TODO text
            tags: Optional list of tags
            is_active: Whether the TODO is active (default: True)
            created_at: Optional creation timestamp (default: current time)
            completed_at: Optional completion timestamp

        Returns:
            ID of the TODO
        """
        with self.get_session() as session:
            todo_data = {"text": text, "tags": tags or [], "is_active": is_active}
            if created_at is not None:
                todo_data["created_at"] = created_at
            if completed_at is not None:
                todo_data["completed_at"] = completed_at
            todo = LocalTODO(**todo_data)
            session.add(todo)
            session.commit()
            session.refresh(todo)
            return int(todo.id)

    def get_local_todos(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get local TODOs.

        Args:
            active_only: If True, only return active TODOs

        Returns:
            List of TODO dictionaries
        """
        with self.get_session() as session:
            stmt = select(LocalTODO).order_by(LocalTODO.created_at.desc())

            if active_only:
                stmt = stmt.where(LocalTODO.is_active == 1)

            todos = session.execute(stmt).scalars().all()

            return [
                {
                    "id": t.id,
                    "text": t.text,
                    "tags": t.tags or [],
                    "is_active": bool(t.is_active),
                    "created_at": t.created_at,
                    "completed_at": t.completed_at,
                }
                for t in todos
            ]

    def get_local_todo(self, todo_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific local TODO.

        Args:
            todo_id: TODO ID

        Returns:
            TODO dictionary or None
        """
        with self.get_session() as session:
            todo = session.get(LocalTODO, todo_id)

            if todo:
                return {
                    "id": todo.id,
                    "text": todo.text,
                    "tags": todo.tags or [],
                    "is_active": bool(todo.is_active),
                    "created_at": todo.created_at,
                    "completed_at": todo.completed_at,
                }

            return None

    def update_local_todo(
        self, todo_id: int, text: Optional[str] = None, tags: Optional[List[str]] = None
    ):
        """Update a local TODO.

        Args:
            todo_id: TODO ID
            text: New text (if provided)
            tags: New tags (if provided)
        """
        with self.get_session() as session:
            todo = session.get(LocalTODO, todo_id)

            if todo:
                if text is not None:
                    todo.text = text
                if tags is not None:
                    todo.tags = tags
                session.commit()

    def complete_local_todo(self, todo_id: int):
        """Mark a local TODO as completed.

        Args:
            todo_id: TODO ID
        """
        with self.get_session() as session:
            todo = session.get(LocalTODO, todo_id)

            if todo:
                todo.is_active = 0
                todo.completed_at = int(datetime.now().timestamp())
                session.commit()

    def activate_local_todo(self, todo_id: int):
        """Reactivate a completed TODO.

        Args:
            todo_id: TODO ID
        """
        with self.get_session() as session:
            todo = session.get(LocalTODO, todo_id)

            if todo:
                todo.is_active = 1
                todo.completed_at = None
                session.commit()

    # Calendar event query
    def get_event_at_time(self, timestamp: int) -> Optional[Dict[str, Any]]:
        """Get calendar event at a specific time.

        Args:
            timestamp: Unix timestamp

        Returns:
            Event dictionary or None
        """
        with self.get_session() as session:
            stmt = (
                select(CalendarEvent)
                .where(
                    and_(CalendarEvent.start_time <= timestamp, CalendarEvent.end_time >= timestamp)
                )
                .order_by(CalendarEvent.start_time)
            )
            event = session.execute(stmt).scalars().first()

            if event:
                return {
                    "id": event.id,
                    "summary": event.summary,
                    "description": event.description,
                    "start_time": event.start_time,
                    "end_time": event.end_time,
                    "location": event.location,
                    "calendar_id": event.calendar_id,
                    "attendees": event.attendees or [],
                    "url": event.url,
                }

            return None

    # GitHub tasks operations
    def upsert_github_task(self, task: Dict[str, Any]):
        """Insert or update a GitHub task.

        Args:
            task: Dictionary with task data
        """
        with self.get_session() as session:
            existing = session.get(GitHubTask, task["id"])

            if existing:
                # Update existing task
                existing.title = task.get("title", existing.title)
                existing.body = task.get("body")
                existing.state = task.get("state", existing.state)
                existing.project_name = task.get("project_name")
                existing.iteration = task.get("iteration")
                existing.assignees = task.get("assignees", [])
                existing.labels = task.get("labels", [])
                existing.url = task.get("url")
                existing.created_at = task.get("created_at")
                existing.updated_at = task.get("updated_at")
                existing.synced_at = int(datetime.now().timestamp())
            else:
                # Create new task
                new_task = GitHubTask(
                    id=task["id"],
                    title=task["title"],
                    body=task.get("body"),
                    state=task["state"],
                    project_name=task.get("project_name"),
                    iteration=task.get("iteration"),
                    assignees=task.get("assignees", []),
                    labels=task.get("labels", []),
                    url=task.get("url"),
                    created_at=task.get("created_at"),
                    updated_at=task.get("updated_at"),
                )
                session.add(new_task)

            session.commit()

    def get_github_tasks(self, iteration: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get GitHub tasks, optionally filtered by iteration.

        Args:
            iteration: Optional iteration name to filter by

        Returns:
            List of task dictionaries
        """
        with self.get_session() as session:
            stmt = select(GitHubTask).order_by(GitHubTask.updated_at.desc())

            if iteration:
                stmt = stmt.where(GitHubTask.iteration == iteration)

            tasks = session.execute(stmt).scalars().all()

            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "body": t.body,
                    "state": t.state,
                    "project_name": t.project_name,
                    "iteration": t.iteration,
                    "assignees": t.assignees or [],
                    "labels": t.labels or [],
                    "url": t.url,
                    "created_at": t.created_at,
                    "updated_at": t.updated_at,
                    "synced_at": t.synced_at,
                }
                for t in tasks
            ]

    def get_github_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific GitHub task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task dictionary or None if not found
        """
        with self.get_session() as session:
            task = session.get(GitHubTask, task_id)

            if not task:
                return None

            return {
                "id": task.id,
                "title": task.title,
                "body": task.body,
                "state": task.state,
                "project_name": task.project_name,
                "iteration": task.iteration,
                "assignees": task.assignees or [],
                "labels": task.labels or [],
                "url": task.url,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "synced_at": task.synced_at,
            }

    # Calendar events operations
    def upsert_calendar_event(self, event: Dict[str, Any]):
        """Insert or update a calendar event.

        Args:
            event: Dictionary with event data
        """
        with self.get_session() as session:
            existing = session.get(CalendarEvent, event["id"])

            if existing:
                # Update existing event
                existing.summary = event.get("summary", existing.summary)
                existing.description = event.get("description")
                existing.start_time = event.get("start_time", existing.start_time)
                existing.end_time = event.get("end_time", existing.end_time)
                existing.location = event.get("location")
                existing.calendar_id = event.get("calendar_id", existing.calendar_id)
                existing.attendees = event.get("attendees", [])
                existing.url = event.get("url")
                existing.synced_at = int(datetime.now().timestamp())
            else:
                # Create new event
                new_event = CalendarEvent(
                    id=event["id"],
                    summary=event["summary"],
                    description=event.get("description"),
                    start_time=event["start_time"],
                    end_time=event["end_time"],
                    location=event.get("location"),
                    calendar_id=event["calendar_id"],
                    attendees=event.get("attendees", []),
                    url=event.get("url"),
                )
                session.add(new_event)

            session.commit()

    def get_calendar_events(self, start_time: int, end_time: int) -> List[Dict[str, Any]]:
        """Get calendar events within a time range.

        Args:
            start_time: Start timestamp (inclusive)
            end_time: End timestamp (inclusive)

        Returns:
            List of event dictionaries
        """
        with self.get_session() as session:
            stmt = (
                select(CalendarEvent)
                .where(
                    and_(CalendarEvent.start_time <= end_time, CalendarEvent.end_time >= start_time)
                )
                .order_by(CalendarEvent.start_time)
            )
            events = session.execute(stmt).scalars().all()

            return [
                {
                    "id": e.id,
                    "summary": e.summary,
                    "description": e.description,
                    "start_time": e.start_time,
                    "end_time": e.end_time,
                    "location": e.location,
                    "calendar_id": e.calendar_id,
                    "attendees": e.attendees or [],
                    "url": e.url,
                    "synced_at": e.synced_at,
                }
                for e in events
            ]

    def get_calendar_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific calendar event by ID.

        Args:
            event_id: Event ID

        Returns:
            Event dictionary or None if not found
        """
        with self.get_session() as session:
            event = session.get(CalendarEvent, event_id)

            if not event:
                return None

            return {
                "id": event.id,
                "summary": event.summary,
                "description": event.description,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "location": event.location,
                "calendar_id": event.calendar_id,
                "attendees": event.attendees or [],
                "url": event.url,
                "synced_at": event.synced_at,
            }

    # Sync metadata operations
    def update_sync_metadata(
        self,
        service: str,
        success: bool = True,
        error_message: Optional[str] = None,
        sync_token: Optional[str] = None,
    ):
        """Update sync metadata for a service.

        Args:
            service: Service name (e.g., 'github', 'gcal')
            success: Whether the sync was successful
            error_message: Optional error message if sync failed
            sync_token: Optional sync token for incremental sync
        """
        with self.get_session() as session:
            now = int(datetime.now().timestamp())
            metadata = session.get(SyncMetadata, service)

            if metadata:
                metadata.last_sync = now
                if success:
                    metadata.last_success = now
                    metadata.error_message = ""
                else:
                    metadata.error_message = error_message
                if sync_token is not None:
                    metadata.sync_token = sync_token
            else:
                metadata = SyncMetadata(
                    service=service,
                    last_sync=now,
                    last_success=now if success else None,
                    error_message=error_message,
                    sync_token=sync_token,
                )
                session.add(metadata)

            session.commit()

    def get_sync_metadata(self, service: str) -> Optional[Dict[str, Any]]:
        """Get sync metadata for a service.

        Args:
            service: Service name

        Returns:
            Metadata dictionary or None if not found
        """
        with self.get_session() as session:
            metadata = session.get(SyncMetadata, service)

            if metadata:
                return {
                    "service": metadata.service,
                    "last_sync": metadata.last_sync,
                    "last_success": metadata.last_success,
                    "error_message": metadata.error_message,
                    "sync_token": metadata.sync_token,
                }
            return None

    # Configuration operations
    def set_config(self, key: str, value: Any):
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value (will be JSON-serialized)
        """
        with self.get_session() as session:
            config = session.get(Config, key)

            if config:
                config.value = json.dumps(value)
                config.updated_at = int(datetime.now().timestamp())
            else:
                config = Config(key=key, value=json.dumps(value))
                session.add(config)

            session.commit()

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        with self.get_session() as session:
            config = session.get(Config, key)

            if config:
                return json.loads(config.value)
            return default

    # Secure credential management
    def _migrate_plaintext_credentials(self):
        """Migrate plaintext credentials from database to secure storage."""
        # Check for plaintext GitHub token
        plaintext_token = self.get_config("github_token")
        if plaintext_token and isinstance(plaintext_token, str):
            # Check if it's not already migrated (migration marker would be a dict)
            if not plaintext_token.startswith("_migrated_"):
                if self._credentials.migrate_plaintext_credential("github_token", plaintext_token):
                    # Mark as migrated in config
                    self.set_config("github_token", "_migrated_to_secure_storage")
                    logger.info("Migrated GitHub token to secure storage")

    def set_github_token(self, token: str):
        """Store GitHub token securely.

        Args:
            token: GitHub personal access token
        """
        self._credentials.set_credential("github_token", token)
        # Update config to mark as using secure storage
        self.set_config("github_token", "_migrated_to_secure_storage")

    def get_github_token(self) -> Optional[str]:
        """Retrieve GitHub token from secure storage.

        Returns:
            GitHub token or None if not set
        """
        # Try secure storage first
        token = self._credentials.get_credential("github_token")
        if token:
            return token

        # Check if there's a plaintext token (backward compatibility)
        config_value: Optional[str] = self.get_config("github_token")
        if config_value and config_value != "_migrated_to_secure_storage":
            # Found plaintext token, migrate it
            self.set_github_token(config_value)
            return str(config_value)

        return None

    def delete_github_token(self):
        """Delete GitHub token from secure storage."""
        self._credentials.delete_credential("github_token")
        self.set_config("github_token", None)

    def get_credential_storage_info(self) -> str:
        """Get information about credential storage backend.

        Returns:
            Human-readable description of storage backend
        """
        return self._credentials.get_storage_info()

    def _resolve_ping_activity(self, ping: Ping, session) -> str:
        """Resolve activity description for a ping.

        Args:
            ping: Ping object
            session: Database session

        Returns:
            Human-readable activity description
        """
        # If no TODO specified, it was dismissed
        if not ping.todo_id:
            return "(Ping dismissed)"

        # Meeting
        if ping.is_meeting or ping.todo_type == "meeting":
            # Try to get event details
            if ping.event_id:
                event = session.get(CalendarEvent, ping.event_id)
                if event:
                    return f"Meeting: {event.summary}"
            return "Meeting"

        # GitHub task
        if ping.todo_type == "github":
            task = session.get(GitHubTask, ping.todo_id)
            if task:
                return f"GitHub: {task.title}"
            return f"GitHub Task (ID: {ping.todo_id})"

        # Local TODO
        if ping.todo_type == "local":
            try:
                todo_id_int = int(ping.todo_id)
                todo = session.get(LocalTODO, todo_id_int)
                if todo:
                    return f"TODO: {todo.text}"
            except (ValueError, TypeError):
                pass
            return f"Local TODO (ID: {ping.todo_id})"

        # Unknown type
        return (
            f"{ping.todo_type}: {ping.todo_id}"
            if ping.todo_type
            else str(ping.todo_id or "Unknown")
        )

    def close(self):
        """Close database connection and clean up thread-local sessions."""
        # Remove thread-local sessions
        self.SessionLocal.remove()
        # Dispose of all connections in the pool
        self.engine.dispose()
