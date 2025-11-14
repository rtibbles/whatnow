"""Main entry point for WhatNow application.

WhatNow is a TagTime-style activity tracker that uses Poisson-distributed
random pings to sample what you're working on throughout the day. This
statistical sampling approach means the fraction of pings tagged with a given
activity approximates the fraction of time spent on that activity.

Key Features:
- Poisson-distributed random pings (default: 45-minute average)
- Integration with GitHub Projects for task tracking
- Integration with Google Calendar for automatic meeting detection
- Local TODO management
- Statistical time analysis and reporting
- Background sync for external data sources
- System tray integration

This module contains the main GTK application class that coordinates all
components: the ping scheduler, sync threads, UI windows, and system tray icon.
"""

import gi

gi.require_version("Gtk", "3.0")
import logging
import signal
import sys
import threading
import time
from datetime import datetime
from typing import Optional

from gi.repository import GLib, Gtk

from .constants import (
    DEFAULT_CALENDAR_DAYS_AHEAD,
    DEFAULT_CALENDAR_IDS,
    DEFAULT_PING_INTERVAL_MINUTES,
    DEFAULT_SYNC_INTERVAL_MINUTES,
    INITIAL_SYNC_DELAY_SECONDS,
    STATUS_MESSAGE_AUTO_CLEAR_SECONDS,
    THREAD_SHUTDOWN_TIMEOUT_SECONDS,
    TOOLTIP_UPDATE_INTERVAL_SECONDS,
)
from .database import Database
from .poisson_scheduler import PoissonScheduler
from .sync.gcal_sync import GoogleCalendarSync
from .sync.github_sync import GitHubSync
from .ui.main_window import MainWindow
from .ui.ping_dialog import show_ping_dialog
from .ui.settings import show_settings_dialog
from .ui.tray_icon import TrayIcon

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhatNowApp(Gtk.Application):
    """Main application class."""

    def __init__(self):
        """Initialize the application."""
        super().__init__(application_id="com.whatnow.app")

        self.db: Optional[Database] = None
        self.scheduler: Optional[PoissonScheduler] = None
        self.main_window: Optional[MainWindow] = None
        self.tray_icon: Optional[TrayIcon] = None
        self.sync_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        self.tooltip_update_timer = None

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def do_activate(self):
        """Handle application activation."""
        if self.main_window:
            # Window already exists, just present it
            self.main_window.present()
            return

        # Initialize database
        self.db = Database()
        logger.info(f"Database initialized at {self.db.db_path}")

        # Check if first run (no settings configured)
        ping_interval = self.db.get_config("ping_interval")
        if ping_interval is None:
            logger.info("First run detected, showing settings dialog")
            self._show_first_run_dialog()

        # Create main window
        self.main_window = MainWindow(self, self.db, on_settings_click=self._on_settings_click)

        # Create system tray icon
        self.tray_icon = TrayIcon(
            on_show=self._on_show_window,
            on_settings=self._on_settings_click,
            on_work_toggle=self._on_work_toggle,
            on_quit=self._on_quit,
        )

        # Check if there's an active work session and restore state
        if self.db.is_working():
            self.tray_icon.set_working_status(True)

        # Start the Poisson scheduler
        self._start_scheduler()

        # Start background sync thread
        self._start_sync_thread()

        # Start tooltip update timer
        self.tooltip_update_timer = GLib.timeout_add_seconds(
            TOOLTIP_UPDATE_INTERVAL_SECONDS, self._update_tray_tooltip
        )
        self._update_tray_tooltip()

        # Show main window
        self.main_window.present()

    def _handle_signal(self, signum, frame):
        """Handle SIGINT and SIGTERM for graceful shutdown.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        # Quit the GTK application
        self.quit()

    def do_shutdown(self):
        """Handle application shutdown."""
        logger.info("Shutting down WhatNow")

        # Signal all threads to stop
        self.shutdown_event.set()

        # Stop tooltip timer
        if self.tooltip_update_timer:
            GLib.source_remove(self.tooltip_update_timer)

        # Stop scheduler
        if self.scheduler:
            logger.info("Stopping ping scheduler...")
            self.scheduler.stop()

        # Stop sync thread
        self.sync_running = False
        if self.sync_thread and self.sync_thread.is_alive():
            logger.info("Waiting for sync thread to finish...")
            self.sync_thread.join(timeout=THREAD_SHUTDOWN_TIMEOUT_SECONDS)
            if self.sync_thread.is_alive():
                logger.warning("Sync thread did not stop gracefully")

        # End work session if active
        if self.db and self.db.is_working():
            self.db.end_work_session()
            logger.info("Ended work session on shutdown")

        # Close database
        if self.db:
            self.db.close()
            logger.info("Database closed")

        Gtk.Application.do_shutdown(self)

    def _show_first_run_dialog(self):
        """Show first run setup dialog."""
        dialog = Gtk.MessageDialog(
            parent=None,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Welcome to WhatNow!",
        )
        dialog.format_secondary_text(
            "This is your first time running WhatNow. "
            "Please configure your settings to get started.\n\n"
            "You can set up:\n"
            "• Ping interval (how often you're asked what you're doing)\n"
            "• GitHub Projects integration (optional)\n"
            "• Google Calendar sync (optional)\n\n"
            "Use the system tray icon to toggle work sessions."
        )
        dialog.run()
        dialog.destroy()

        # Show settings
        self._show_settings()

    def _start_scheduler(self):
        """Start the Poisson ping scheduler."""
        ping_interval = self.db.get_config("ping_interval", DEFAULT_PING_INTERVAL_MINUTES)

        self.scheduler = PoissonScheduler(
            average_gap_minutes=ping_interval, ping_callback=self._on_ping_triggered
        )
        self.scheduler.start()

        logger.info(f"Poisson scheduler started with {ping_interval} minute average gap")

    def _on_ping_triggered(self, timestamp: int):
        """Handle when a ping is triggered.

        Args:
            timestamp: Unix timestamp of the ping
        """
        logger.info(f"Ping triggered at timestamp {timestamp}")

        # Show ping dialog on main thread
        GLib.idle_add(self._show_ping_dialog, timestamp)

    def _show_ping_dialog(self, timestamp: int):
        """Show the ping dialog (called on main thread).

        Args:
            timestamp: Unix timestamp of the ping
        """
        assert self.db is not None, "Database must be initialized"

        # Check if currently working
        if not self.db.is_working():
            logger.info("Skipping ping - not in active work session")
            return False

        # Check for meeting at this time
        event = self.db.get_event_at_time(timestamp)
        if event:
            # Auto-log meeting silently
            logger.info(f"Auto-logging meeting: {event['summary']}")
            self.db.add_ping(
                timestamp=timestamp,
                todo_id=event["id"],
                todo_type="meeting",
                tags=["meeting"],
                notes=event["summary"],
                event_id=event["id"],
                is_meeting=True,
            )
            return False

        # Get current iteration GitHub tasks
        github_tasks = self.db.get_github_tasks()

        # Get active local TODOs
        local_todos = self.db.get_local_todos(active_only=True)

        def on_ping_submitted(
            ts: int, todo_id: str, todo_type: str, tags: list, notes: Optional[str]
        ):
            """Handle ping submission."""
            assert self.db is not None  # Already checked in parent function
            try:
                ping_id = self.db.add_ping(
                    timestamp=ts, todo_id=todo_id, todo_type=todo_type, tags=tags, notes=notes
                )
                logger.info(f"Ping saved with ID {ping_id}: {todo_type}/{todo_id}")

                # Refresh main window
                if self.main_window:
                    GLib.idle_add(self.main_window.refresh_all)

            except Exception as e:
                logger.error(f"Error saving ping: {e}")

        # Show dialog
        show_ping_dialog(
            self.main_window, timestamp, github_tasks, local_todos, self.db, on_ping_submitted
        )

        return False  # Don't repeat

    def _start_sync_thread(self):
        """Start background sync thread."""
        self.sync_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=False)
        self.sync_thread.start()
        logger.info("Background sync thread started")

    def _sync_loop(self):
        """Background sync loop."""
        # Wait a bit before first sync (interruptible)
        if self.shutdown_event.wait(timeout=INITIAL_SYNC_DELAY_SECONDS):
            return  # Shutdown requested during initial wait

        while self.sync_running and not self.shutdown_event.is_set():
            try:
                sync_interval = self.db.get_config("sync_interval", DEFAULT_SYNC_INTERVAL_MINUTES)
                logger.info("Running background sync")

                # Sync GitHub if configured
                github_connected = self.db.get_config("github_connected", False)
                github_org = self.db.get_config("github_org")
                github_project = self.db.get_config("github_project")

                if github_connected and github_org and github_project:
                    try:
                        # Show sync status
                        GLib.idle_add(self._set_sync_status, "Syncing GitHub...")

                        github_sync = GitHubSync(self.db, github_org, github_project)
                        if github_sync.sync():
                            # Update main window
                            GLib.idle_add(self._refresh_github_tasks)
                            GLib.idle_add(self._set_sync_status, "GitHub synced")
                        else:
                            GLib.idle_add(self._set_sync_status, "GitHub sync failed")
                    except Exception as e:
                        logger.error(f"GitHub sync error: {e}")
                        GLib.idle_add(self._set_sync_status, f"GitHub sync error: {str(e)[:50]}")

                # Check for shutdown before continuing
                if self.shutdown_event.is_set():
                    break

                # Sync Google Calendar if configured
                gcal_connected = self.db.get_config("gcal_connected", False)
                gcal_ids = self.db.get_config("gcal_calendar_ids", DEFAULT_CALENDAR_IDS)

                if gcal_connected:
                    try:
                        # Show sync status
                        GLib.idle_add(self._set_sync_status, "Syncing Calendar...")

                        gcal_sync = GoogleCalendarSync(self.db, gcal_ids)
                        if gcal_sync.sync():
                            # Update main window
                            GLib.idle_add(self._refresh_calendar_events)
                            GLib.idle_add(self._set_sync_status, "Calendar synced")
                        else:
                            GLib.idle_add(self._set_sync_status, "Calendar sync failed")
                    except Exception as e:
                        logger.error(f"Google Calendar sync error: {e}")
                        GLib.idle_add(self._set_sync_status, f"Calendar sync error: {str(e)[:50]}")

                # Wait for next sync (interruptible)
                if self.shutdown_event.wait(timeout=sync_interval * 60):
                    break  # Shutdown requested during wait

            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                # Wait a minute before retrying (interruptible)
                if self.shutdown_event.wait(timeout=60):
                    break

        logger.info("Sync loop ended")

    def _set_sync_status(self, message: str):
        """Set sync status message in main window.

        Args:
            message: Status message to display
        """
        if self.main_window:
            self.main_window.set_status(message)
            # Auto-clear after a few seconds
            GLib.timeout_add_seconds(
                STATUS_MESSAGE_AUTO_CLEAR_SECONDS, self.main_window.clear_status
            )
        return False

    def _refresh_github_tasks(self):
        """Refresh GitHub tasks in main window."""
        if self.main_window:
            self.main_window.refresh_tasks()
        return False

    def _refresh_calendar_events(self):
        """Refresh calendar events in main window."""
        if self.main_window:
            self.main_window.refresh_events()
        return False

    def _update_tray_tooltip(self):
        """Update system tray tooltip with current hours."""
        if not self.tray_icon:
            return True

        try:
            # Get today's timestamp
            now = datetime.now()
            today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
            today_ts = int(today_start.timestamp())

            # Get total work seconds for today
            total_seconds = self.db.get_total_work_seconds_for_day(today_ts)
            hours = total_seconds / 3600.0

            # Update tooltip
            self.tray_icon.update_tooltip_with_time(hours)

        except Exception as e:
            logger.error(f"Error updating tray tooltip: {e}")

        return True  # Continue timer

    def _on_work_toggle(self, is_working: bool):
        """Handle work toggle from tray icon.

        Args:
            is_working: Whether work session is starting
        """
        assert self.db is not None, "Database must be initialized"

        if is_working:
            # Start work session
            session_id = self.db.start_work_session()
            logger.info(f"Started work session {session_id}")
        else:
            # End work session
            total_seconds = self.db.end_work_session()
            if total_seconds:
                hours = total_seconds / 3600.0
                logger.info(f"Ended work session: {hours:.2f} hours")

        # Update tooltip immediately
        self._update_tray_tooltip()

    def _on_show_window(self):
        """Show main window."""
        if self.main_window:
            self.main_window.present()

    def _on_settings_click(self):
        """Show settings dialog."""
        self._show_settings()

    def _show_settings(self):
        """Show settings dialog."""
        saved = show_settings_dialog(self.main_window, self.db)

        if saved:
            # Update scheduler with new ping interval
            ping_interval = self.db.get_config("ping_interval", 45)
            if self.scheduler:
                self.scheduler.set_average_gap(ping_interval)

            logger.info("Settings saved and applied")

    def _on_quit(self):
        """Handle quit request."""
        self.quit()


def main():
    """Main entry point."""
    app = WhatNowApp()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)


if __name__ == "__main__":
    main()
