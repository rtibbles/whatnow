"""Initial schema baseline

Revision ID: 001_initial
Revises:
Create Date: 2025-11-13 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""
    # Pings table
    op.create_table(
        "pings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.Integer(), nullable=False),
        sa.Column("todo_id", sa.String(), nullable=True),
        sa.Column("todo_type", sa.String(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("event_id", sa.String(), nullable=True),
        sa.Column("is_meeting", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pings_timestamp"), "pings", ["timestamp"], unique=False)
    op.create_index(op.f("ix_pings_todo"), "pings", ["todo_id", "todo_type"], unique=False)

    # Work sessions table
    op.create_table(
        "work_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Integer(), nullable=False),
        sa.Column("end_time", sa.Integer(), nullable=True),
        sa.Column("total_seconds", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_work_sessions_end_time"), "work_sessions", ["end_time"], unique=False
    )

    # Local TODOs table
    op.create_table(
        "local_todos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("urgency", sa.Integer(), nullable=False),  # 1-4: Low, Medium, High, Urgent
        sa.Column("importance", sa.Integer(), nullable=False),  # 1-4: Low, Medium, High, Critical
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_local_todos_active"), "local_todos", ["is_active"], unique=False
    )
    op.create_index(
        op.f("ix_local_todos_priority"), "local_todos", ["urgency", "importance"], unique=False
    )

    # GitHub tasks table
    op.create_table(
        "github_tasks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("project_name", sa.String(), nullable=True),
        sa.Column("iteration", sa.String(), nullable=True),
        sa.Column("urgency", sa.Integer(), nullable=True),  # 1-4: Low, Medium, High, Urgent
        sa.Column("importance", sa.Integer(), nullable=True),  # 1-4: Low, Medium, High, Critical
        sa.Column("assignees", sa.JSON(), nullable=True),
        sa.Column("labels", sa.JSON(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("created_at", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.Integer(), nullable=True),
        sa.Column("synced_at", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_github_tasks_iteration"), "github_tasks", ["iteration"], unique=False
    )
    op.create_index(
        op.f("ix_github_tasks_priority"), "github_tasks", ["urgency", "importance"], unique=False
    )

    # Calendar events table
    op.create_table(
        "calendar_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("start_time", sa.Integer(), nullable=False),
        sa.Column("end_time", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("calendar_id", sa.String(), nullable=False),
        sa.Column("attendees", sa.JSON(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("synced_at", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_calendar_events_end_time"), "calendar_events", ["end_time"], unique=False
    )
    op.create_index(
        op.f("ix_calendar_events_start_time"), "calendar_events", ["start_time"], unique=False
    )
    op.create_index(
        op.f("ix_calendar_events_time_range"), "calendar_events", ["start_time", "end_time"], unique=False
    )

    # Sync metadata table
    op.create_table(
        "sync_metadata",
        sa.Column("service", sa.String(), nullable=False),
        sa.Column("last_sync", sa.Integer(), nullable=False),
        sa.Column("last_success", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("sync_token", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("service"),
    )

    # Config table
    op.create_table(
        "config",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("updated_at", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("config")
    op.drop_table("sync_metadata")
    op.drop_index(op.f("ix_calendar_events_time_range"), table_name="calendar_events")
    op.drop_index(op.f("ix_calendar_events_start_time"), table_name="calendar_events")
    op.drop_index(op.f("ix_calendar_events_end_time"), table_name="calendar_events")
    op.drop_table("calendar_events")
    op.drop_index(op.f("ix_github_tasks_priority"), table_name="github_tasks")
    op.drop_index(op.f("ix_github_tasks_iteration"), table_name="github_tasks")
    op.drop_table("github_tasks")
    op.drop_index(op.f("ix_local_todos_priority"), table_name="local_todos")
    op.drop_index(op.f("ix_local_todos_active"), table_name="local_todos")
    op.drop_table("local_todos")
    op.drop_index(op.f("ix_work_sessions_end_time"), table_name="work_sessions")
    op.drop_table("work_sessions")
    op.drop_index(op.f("ix_pings_todo"), table_name="pings")
    op.drop_index(op.f("ix_pings_timestamp"), table_name="pings")
    op.drop_table("pings")
