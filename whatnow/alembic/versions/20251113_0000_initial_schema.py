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

    # Work sessions table
    op.create_table(
        "work_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Integer(), nullable=False),
        sa.Column("end_time", sa.Integer(), nullable=True),
        sa.Column("total_seconds", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Local TODOs table
    op.create_table(
        "local_todos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # GitHub tasks table
    op.create_table(
        "github_tasks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("labels", sa.JSON(), nullable=True),
        sa.Column("assignees", sa.JSON(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.Integer(), nullable=False),
        sa.Column("iteration_title", sa.String(), nullable=True),
        sa.Column("last_synced", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
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
        sa.Column("last_synced", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_calendar_events_end_time"), "calendar_events", ["end_time"], unique=False
    )
    op.create_index(
        op.f("ix_calendar_events_start_time"), "calendar_events", ["start_time"], unique=False
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
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("config")
    op.drop_table("sync_metadata")
    op.drop_index(op.f("ix_calendar_events_start_time"), table_name="calendar_events")
    op.drop_index(op.f("ix_calendar_events_end_time"), table_name="calendar_events")
    op.drop_table("calendar_events")
    op.drop_table("github_tasks")
    op.drop_table("local_todos")
    op.drop_table("work_sessions")
    op.drop_index(op.f("ix_pings_timestamp"), table_name="pings")
    op.drop_table("pings")
