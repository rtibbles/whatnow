"""SQLAlchemy models for WhatNow."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Ping(Base):
    """TagTime activity ping."""

    __tablename__ = "pings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    todo_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    todo_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # 'github', 'local', 'meeting'
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Calendar event ID if meeting
    is_meeting: Mapped[bool] = mapped_column(
        Integer, nullable=False, default=0
    )  # SQLite uses 0/1 for bool
    created_at: Mapped[int] = mapped_column(
        Integer, nullable=False, default=lambda: int(datetime.now().timestamp())
    )

    def __repr__(self) -> str:
        return f"<Ping(id={self.id}, timestamp={self.timestamp}, todo_type='{self.todo_type}')>"


class GitHubTask(Base):
    """GitHub Projects task/issue."""

    __tablename__ = "github_tasks"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    project_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    iteration: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    urgency: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # 1=Low, 2=Medium, 3=High, 4=Urgent
    importance: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # 1=Low, 2=Medium, 3=High, 4=Critical
    assignees: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    labels: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    synced_at: Mapped[int] = mapped_column(
        Integer, nullable=False, default=lambda: int(datetime.now().timestamp())
    )

    def __repr__(self) -> str:
        return f"<GitHubTask(id='{self.id}', title='{self.title}', state='{self.state}')>"


class CalendarEvent(Base):
    """Google Calendar event."""

    __tablename__ = "calendar_events"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_time: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    end_time: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    calendar_id: Mapped[str] = mapped_column(String(255), nullable=False)
    attendees: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    synced_at: Mapped[int] = mapped_column(
        Integer, nullable=False, default=lambda: int(datetime.now().timestamp())
    )

    def __repr__(self) -> str:
        return f"<CalendarEvent(id='{self.id}', summary='{self.summary}')>"


class SyncMetadata(Base):
    """Sync metadata for external services."""

    __tablename__ = "sync_metadata"

    service: Mapped[str] = mapped_column(String(50), primary_key=True)
    last_sync: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_success: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sync_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SyncMetadata(service='{self.service}', last_sync={self.last_sync})>"


class Config(Base):
    """Application configuration."""

    __tablename__ = "config"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=lambda: int(datetime.now().timestamp()),
        onupdate=lambda: int(datetime.now().timestamp()),
    )

    def __repr__(self) -> str:
        return f"<Config(key='{self.key}')>"


class WorkSession(Base):
    """Work session tracking."""

    __tablename__ = "work_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start_time: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    end_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<WorkSession(id={self.id}, start={self.start_time}, end={self.end_time})>"


class LocalTODO(Base):
    """Local TODO item."""

    __tablename__ = "local_todos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Integer, nullable=False, default=1
    )  # SQLite uses 0/1 for bool
    urgency: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2
    )  # 1=Low, 2=Medium, 3=High, 4=Urgent
    importance: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2
    )  # 1=Low, 2=Medium, 3=High, 4=Critical
    created_at: Mapped[int] = mapped_column(
        Integer, nullable=False, default=lambda: int(datetime.now().timestamp())
    )
    completed_at: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<LocalTODO(id={self.id}, text='{self.text}', active={self.is_active})>"
