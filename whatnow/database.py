"""Database management for WhatNow using SQLAlchemy."""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import json

from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, Ping, GitHubTask, CalendarEvent, SyncMetadata, Config


class Database:
    """SQLAlchemy database manager for local-first storage."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Use XDG_DATA_HOME or default to ~/.local/share
            data_dir = os.environ.get('XDG_DATA_HOME',
                                     os.path.expanduser('~/.local/share'))
            app_dir = Path(data_dir) / 'whatnow'
            app_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(app_dir / 'whatnow.db')

        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Create all tables
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get a new database session.

        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()

    # Ping operations
    def add_ping(self, timestamp: int, activity: str, tags: Optional[List[str]] = None,
                 notes: Optional[str] = None) -> int:
        """Add a new ping to the database.

        Args:
            timestamp: Unix timestamp of the ping
            activity: Activity description
            tags: Optional list of tags
            notes: Optional additional notes

        Returns:
            ID of the inserted ping
        """
        with self.get_session() as session:
            ping = Ping(
                timestamp=timestamp,
                activity=activity,
                tags=tags,
                notes=notes
            )
            session.add(ping)
            session.commit()
            session.refresh(ping)
            return ping.id

    def get_pings(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get recent pings.

        Args:
            limit: Maximum number of pings to return
            offset: Number of pings to skip

        Returns:
            List of ping dictionaries
        """
        with self.get_session() as session:
            stmt = select(Ping).order_by(Ping.timestamp.desc()).limit(limit).offset(offset)
            pings = session.execute(stmt).scalars().all()

            return [
                {
                    'id': p.id,
                    'timestamp': p.timestamp,
                    'activity': p.activity,
                    'tags': p.tags or [],
                    'notes': p.notes,
                    'created_at': p.created_at
                }
                for p in pings
            ]

    def get_pings_by_date_range(self, start_time: int, end_time: int) -> List[Dict[str, Any]]:
        """Get pings within a date range.

        Args:
            start_time: Start timestamp (inclusive)
            end_time: End timestamp (inclusive)

        Returns:
            List of ping dictionaries
        """
        with self.get_session() as session:
            stmt = (
                select(Ping)
                .where(and_(Ping.timestamp >= start_time, Ping.timestamp <= end_time))
                .order_by(Ping.timestamp.desc())
            )
            pings = session.execute(stmt).scalars().all()

            return [
                {
                    'id': p.id,
                    'timestamp': p.timestamp,
                    'activity': p.activity,
                    'tags': p.tags or [],
                    'notes': p.notes,
                    'created_at': p.created_at
                }
                for p in pings
            ]

    # GitHub tasks operations
    def upsert_github_task(self, task: Dict[str, Any]):
        """Insert or update a GitHub task.

        Args:
            task: Dictionary with task data
        """
        with self.get_session() as session:
            existing = session.get(GitHubTask, task['id'])

            if existing:
                # Update existing task
                existing.title = task.get('title', existing.title)
                existing.body = task.get('body')
                existing.state = task.get('state', existing.state)
                existing.project_name = task.get('project_name')
                existing.iteration = task.get('iteration')
                existing.assignees = task.get('assignees', [])
                existing.labels = task.get('labels', [])
                existing.url = task.get('url')
                existing.created_at = task.get('created_at')
                existing.updated_at = task.get('updated_at')
                existing.synced_at = int(datetime.now().timestamp())
            else:
                # Create new task
                new_task = GitHubTask(
                    id=task['id'],
                    title=task['title'],
                    body=task.get('body'),
                    state=task['state'],
                    project_name=task.get('project_name'),
                    iteration=task.get('iteration'),
                    assignees=task.get('assignees', []),
                    labels=task.get('labels', []),
                    url=task.get('url'),
                    created_at=task.get('created_at'),
                    updated_at=task.get('updated_at')
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
                    'id': t.id,
                    'title': t.title,
                    'body': t.body,
                    'state': t.state,
                    'project_name': t.project_name,
                    'iteration': t.iteration,
                    'assignees': t.assignees or [],
                    'labels': t.labels or [],
                    'url': t.url,
                    'created_at': t.created_at,
                    'updated_at': t.updated_at,
                    'synced_at': t.synced_at
                }
                for t in tasks
            ]

    # Calendar events operations
    def upsert_calendar_event(self, event: Dict[str, Any]):
        """Insert or update a calendar event.

        Args:
            event: Dictionary with event data
        """
        with self.get_session() as session:
            existing = session.get(CalendarEvent, event['id'])

            if existing:
                # Update existing event
                existing.summary = event.get('summary', existing.summary)
                existing.description = event.get('description')
                existing.start_time = event.get('start_time', existing.start_time)
                existing.end_time = event.get('end_time', existing.end_time)
                existing.location = event.get('location')
                existing.calendar_id = event.get('calendar_id', existing.calendar_id)
                existing.attendees = event.get('attendees', [])
                existing.url = event.get('url')
                existing.synced_at = int(datetime.now().timestamp())
            else:
                # Create new event
                new_event = CalendarEvent(
                    id=event['id'],
                    summary=event['summary'],
                    description=event.get('description'),
                    start_time=event['start_time'],
                    end_time=event['end_time'],
                    location=event.get('location'),
                    calendar_id=event['calendar_id'],
                    attendees=event.get('attendees', []),
                    url=event.get('url')
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
                .where(and_(
                    CalendarEvent.start_time <= end_time,
                    CalendarEvent.end_time >= start_time
                ))
                .order_by(CalendarEvent.start_time)
            )
            events = session.execute(stmt).scalars().all()

            return [
                {
                    'id': e.id,
                    'summary': e.summary,
                    'description': e.description,
                    'start_time': e.start_time,
                    'end_time': e.end_time,
                    'location': e.location,
                    'calendar_id': e.calendar_id,
                    'attendees': e.attendees or [],
                    'url': e.url,
                    'synced_at': e.synced_at
                }
                for e in events
            ]

    # Sync metadata operations
    def update_sync_metadata(self, service: str, success: bool = True,
                            error_message: Optional[str] = None,
                            sync_token: Optional[str] = None):
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
                    metadata.error_message = None
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
                    sync_token=sync_token
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
                    'service': metadata.service,
                    'last_sync': metadata.last_sync,
                    'last_success': metadata.last_success,
                    'error_message': metadata.error_message,
                    'sync_token': metadata.sync_token
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

    def close(self):
        """Close database connection."""
        self.engine.dispose()
