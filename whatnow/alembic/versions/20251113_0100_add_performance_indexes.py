"""Add performance indexes

Revision ID: 002_indexes
Revises: 001_initial
Create Date: 2025-11-13 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_indexes'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes for frequently queried columns."""
    # Composite index for calendar event time range queries
    # Improves: "SELECT * FROM calendar_events WHERE start_time <= X AND end_time >= Y"
    op.create_index(
        'ix_calendar_events_time_range',
        'calendar_events',
        ['start_time', 'end_time']
    )

    # Index on GitHub tasks iteration_title for filtering current iteration
    op.create_index(
        'ix_github_tasks_iteration',
        'github_tasks',
        ['iteration_title']
    )

    # Index on pings todo_id for faster activity resolution
    op.create_index(
        'ix_pings_todo',
        'pings',
        ['todo_id', 'todo_type']
    )

    # Index on local_todos is_active for filtering active todos
    op.create_index(
        'ix_local_todos_active',
        'local_todos',
        ['is_active']
    )

    # Index on work_sessions end_time for finding active sessions
    op.create_index(
        'ix_work_sessions_end_time',
        'work_sessions',
        ['end_time']
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index('ix_work_sessions_end_time', table_name='work_sessions')
    op.drop_index('ix_local_todos_active', table_name='local_todos')
    op.drop_index('ix_pings_todo', table_name='pings')
    op.drop_index('ix_github_tasks_iteration', table_name='github_tasks')
    op.drop_index('ix_calendar_events_time_range', table_name='calendar_events')
