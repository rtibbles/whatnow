"""Settings dialog for configuration."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from typing import Optional

from ..constants import (
    DEFAULT_PING_INTERVAL_MINUTES,
    MIN_PING_INTERVAL_MINUTES,
    MAX_PING_INTERVAL_MINUTES,
    PING_INTERVAL_INCREMENT,
    PING_INTERVAL_LARGE_INCREMENT,
    DEFAULT_SYNC_INTERVAL_MINUTES,
    MIN_SYNC_INTERVAL_MINUTES,
    MAX_SYNC_INTERVAL_MINUTES,
    SYNC_INTERVAL_INCREMENT,
    SYNC_INTERVAL_LARGE_INCREMENT,
    POISSON_DISTRIBUTION_NOTE,
    DEFAULT_CALENDAR_IDS,
)


class SettingsDialog(Gtk.Dialog):
    """Settings dialog for API tokens and preferences."""

    def __init__(self, parent: Optional[Gtk.Window], db):
        """Initialize the settings dialog.

        Args:
            parent: Parent window
            db: Database instance
        """
        super().__init__(
            title="Settings",
            parent=parent,
            modal=True,
            destroy_with_parent=True
        )

        self.db = db

        # Set dialog size
        self.set_default_size(600, 500)
        self.set_border_width(10)

        # Add buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        # Create content
        content_area = self.get_content_area()
        content_area.set_spacing(10)

        # Create notebook for different settings categories
        notebook = Gtk.Notebook()
        content_area.pack_start(notebook, True, True, 0)

        # Create settings pages
        self._create_general_page(notebook)
        self._create_github_page(notebook)
        self._create_calendar_page(notebook)
        self._create_backup_page(notebook)

        # Load current settings
        self._load_settings()

        # Show all widgets
        self.show_all()

    def _create_general_page(self, notebook: Gtk.Notebook):
        """Create the general settings page."""
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_border_width(10)

        row = 0

        # Ping interval
        label = Gtk.Label(label="Average ping interval (minutes):", xalign=0)
        grid.attach(label, 0, row, 1, 1)

        self.ping_interval_spin = Gtk.SpinButton()
        self.ping_interval_spin.set_range(MIN_PING_INTERVAL_MINUTES, MAX_PING_INTERVAL_MINUTES)
        self.ping_interval_spin.set_increments(PING_INTERVAL_INCREMENT, PING_INTERVAL_LARGE_INCREMENT)
        self.ping_interval_spin.set_value(DEFAULT_PING_INTERVAL_MINUTES)
        grid.attach(self.ping_interval_spin, 1, row, 1, 1)

        row += 1

        # Info label
        info_label = Gtk.Label()
        info_label.set_markup(f"<small>{POISSON_DISTRIBUTION_NOTE}</small>")
        info_label.set_line_wrap(True)
        info_label.set_xalign(0)
        grid.attach(info_label, 0, row, 2, 1)

        row += 1

        # Sync interval
        label = Gtk.Label(label="Sync interval (minutes):", xalign=0)
        grid.attach(label, 0, row, 1, 1)

        self.sync_interval_spin = Gtk.SpinButton()
        self.sync_interval_spin.set_range(MIN_SYNC_INTERVAL_MINUTES, MAX_SYNC_INTERVAL_MINUTES)
        self.sync_interval_spin.set_increments(SYNC_INTERVAL_INCREMENT, SYNC_INTERVAL_LARGE_INCREMENT)
        self.sync_interval_spin.set_value(DEFAULT_SYNC_INTERVAL_MINUTES)
        grid.attach(self.sync_interval_spin, 1, row, 1, 1)

        # Add to notebook
        label = Gtk.Label(label="General")
        notebook.append_page(grid, label)

    def _create_github_page(self, notebook: Gtk.Notebook):
        """Create the GitHub settings page."""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(10)

        # Instructions
        info_label = Gtk.Label()
        info_label.set_markup(
            "<b>GitHub Personal Access Token</b>\n\n"
            "1. Go to GitHub Settings → Developer Settings → Personal Access Tokens\n"
            "2. Create a token with <tt>repo</tt> and <tt>project</tt> scopes\n"
            "3. Paste the token below"
        )
        info_label.set_line_wrap(True)
        info_label.set_xalign(0)
        vbox.pack_start(info_label, False, False, 0)

        # Token entry
        token_label = Gtk.Label(label="Personal Access Token:", xalign=0)
        vbox.pack_start(token_label, False, False, 0)

        self.github_token_entry = Gtk.Entry()
        self.github_token_entry.set_placeholder_text("ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        self.github_token_entry.set_visibility(False)
        self.github_token_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        vbox.pack_start(self.github_token_entry, False, False, 0)

        # Show token checkbox
        self.show_github_token = Gtk.CheckButton(label="Show token")
        self.show_github_token.connect("toggled", self._on_show_github_token_toggled)
        vbox.pack_start(self.show_github_token, False, False, 0)

        # Separator
        vbox.pack_start(Gtk.Separator(), False, False, 5)

        # Organization
        org_label = Gtk.Label(label="GitHub Organization/User:", xalign=0)
        vbox.pack_start(org_label, False, False, 0)

        self.github_org_entry = Gtk.Entry()
        self.github_org_entry.set_placeholder_text("e.g., myorg or myusername")
        vbox.pack_start(self.github_org_entry, False, False, 0)

        # Project number
        project_label = Gtk.Label(label="Project Number:", xalign=0)
        vbox.pack_start(project_label, False, False, 0)

        self.github_project_spin = Gtk.SpinButton()
        self.github_project_spin.set_range(1, 10000)
        self.github_project_spin.set_increments(1, 10)
        self.github_project_spin.set_value(1)
        vbox.pack_start(self.github_project_spin, False, False, 0)

        # Separator
        vbox.pack_start(Gtk.Separator(), False, False, 5)

        # Test connection button
        test_button = Gtk.Button(label="Test Connection")
        test_button.connect("clicked", self._on_test_github_clicked)
        vbox.pack_start(test_button, False, False, 0)

        # Sync status
        self.github_status_label = Gtk.Label()
        self.github_status_label.set_xalign(0)
        vbox.pack_start(self.github_status_label, False, False, 5)

        # Add to notebook
        label = Gtk.Label(label="GitHub")
        notebook.append_page(vbox, label)

    def _create_calendar_page(self, notebook: Gtk.Notebook):
        """Create the Google Calendar settings page."""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(10)

        # Instructions
        info_label = Gtk.Label()
        info_label.set_markup(
            "<b>Google Calendar Integration</b>\n\n"
            "Connect your Google Calendar to automatically detect meetings.\n"
            "During meetings, pings will be silently logged without interrupting you."
        )
        info_label.set_line_wrap(True)
        info_label.set_xalign(0)
        vbox.pack_start(info_label, False, False, 0)

        # Connection status
        self.gcal_status_label = Gtk.Label()
        self.gcal_status_label.set_xalign(0)
        vbox.pack_start(self.gcal_status_label, False, False, 5)

        # Connect button
        connect_button = Gtk.Button(label="Connect Google Calendar")
        connect_button.connect("clicked", self._on_connect_calendar_clicked)
        vbox.pack_start(connect_button, False, False, 0)

        # Separator
        vbox.pack_start(Gtk.Separator(), False, False, 5)

        # Calendar IDs
        cal_label = Gtk.Label()
        cal_label.set_markup(
            "Calendar IDs to sync (one per line):\n"
            "<small>Use 'primary' for your main calendar or specific calendar IDs</small>"
        )
        cal_label.set_xalign(0)
        vbox.pack_start(cal_label, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(150)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.gcal_ids_textview = Gtk.TextView()
        self.gcal_ids_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.add(self.gcal_ids_textview)
        vbox.pack_start(scrolled, True, True, 0)

        # Add to notebook
        label = Gtk.Label(label="Google Calendar")
        notebook.append_page(vbox, label)

    def _create_backup_page(self, notebook: Gtk.Notebook):
        """Create the backup and data safety page."""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(10)

        # Instructions
        info_label = Gtk.Label()
        info_label.set_markup(
            "<b>Database Backup & Data Export</b>\n\n"
            "Backups are automatically created before database migrations.\n"
            "You can also create manual backups or export your data to JSON."
        )
        info_label.set_line_wrap(True)
        info_label.set_xalign(0)
        vbox.pack_start(info_label, False, False, 0)

        # Create backup button
        backup_button = Gtk.Button(label="Create Backup Now")
        backup_button.connect("clicked", self._on_create_backup_clicked)
        vbox.pack_start(backup_button, False, False, 0)

        # Export data button
        export_button = Gtk.Button(label="Export Data to JSON")
        export_button.connect("clicked", self._on_export_data_clicked)
        vbox.pack_start(export_button, False, False, 0)

        # Separator
        vbox.pack_start(Gtk.Separator(), False, False, 5)

        # Backup status label
        self.backup_status_label = Gtk.Label()
        self.backup_status_label.set_xalign(0)
        vbox.pack_start(self.backup_status_label, False, False, 5)

        # Add to notebook
        label = Gtk.Label(label="Backup & Data")
        notebook.append_page(vbox, label)

    def _load_settings(self):
        """Load current settings from database."""
        # General settings
        ping_interval = self.db.get_config('ping_interval', 45)
        self.ping_interval_spin.set_value(ping_interval)

        sync_interval = self.db.get_config('sync_interval', 30)
        self.sync_interval_spin.set_value(sync_interval)

        # GitHub settings
        github_token = self.db.get_github_token() or ''
        self.github_token_entry.set_text(github_token)

        github_org = self.db.get_config('github_org', '')
        self.github_org_entry.set_text(github_org)

        github_project = self.db.get_config('github_project', 1)
        self.github_project_spin.set_value(github_project)

        # GitHub sync status
        github_sync_meta = self.db.get_sync_metadata('github')
        if github_sync_meta:
            from datetime import datetime
            last_sync = github_sync_meta.get('last_sync')
            if last_sync:
                last_sync_dt = datetime.fromtimestamp(last_sync)
                last_sync_str = last_sync_dt.strftime('%Y-%m-%d %H:%M:%S')
                success = github_sync_meta.get('success', False)
                if success:
                    self.github_status_label.set_markup(
                        f"<small>Last synced: {last_sync_str}</small>"
                    )
                else:
                    error_msg = github_sync_meta.get('error_message', 'Unknown error')
                    self.github_status_label.set_markup(
                        f"<small><span color='red'>Last sync failed: {error_msg[:50]}</span>\n"
                        f"Time: {last_sync_str}</small>"
                    )

        # Google Calendar settings
        gcal_connected = self.db.get_config('gcal_connected', False)
        gcal_sync_meta = self.db.get_sync_metadata('gcal')

        if gcal_connected:
            status_text = "<span color='green'>✓ Connected</span>"
            if gcal_sync_meta:
                from datetime import datetime
                last_sync = gcal_sync_meta.get('last_sync')
                if last_sync:
                    last_sync_dt = datetime.fromtimestamp(last_sync)
                    last_sync_str = last_sync_dt.strftime('%Y-%m-%d %H:%M:%S')
                    success = gcal_sync_meta.get('success', False)
                    if success:
                        status_text += f"\n<small>Last synced: {last_sync_str}</small>"
                    else:
                        error_msg = gcal_sync_meta.get('error_message', 'Unknown error')
                        status_text += f"\n<small><span color='red'>Last sync failed: {error_msg[:50]}</span></small>"
            self.gcal_status_label.set_markup(status_text)
        else:
            self.gcal_status_label.set_markup("<span color='gray'>Not connected</span>")

        gcal_ids = self.db.get_config('gcal_calendar_ids', DEFAULT_CALENDAR_IDS)
        gcal_ids_text = '\n'.join(gcal_ids)
        buffer = self.gcal_ids_textview.get_buffer()
        buffer.set_text(gcal_ids_text)

    def _save_settings(self):
        """Save settings to database."""
        # General settings
        self.db.set_config('ping_interval', self.ping_interval_spin.get_value())
        self.db.set_config('sync_interval', self.sync_interval_spin.get_value())

        # GitHub settings
        token_text = self.github_token_entry.get_text().strip()
        if token_text:
            self.db.set_github_token(token_text)
        else:
            self.db.delete_github_token()
        self.db.set_config('github_org', self.github_org_entry.get_text().strip())
        self.db.set_config('github_project', int(self.github_project_spin.get_value()))

        # Google Calendar settings
        buffer = self.gcal_ids_textview.get_buffer()
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()
        gcal_ids_text = buffer.get_text(start_iter, end_iter, True)
        gcal_ids = [line.strip() for line in gcal_ids_text.split('\n') if line.strip()]
        self.db.set_config('gcal_calendar_ids', gcal_ids or ['primary'])

    def _on_show_github_token_toggled(self, checkbox):
        """Toggle GitHub token visibility."""
        self.github_token_entry.set_visibility(checkbox.get_active())

    def _on_connect_calendar_clicked(self, button):
        """Handle Google Calendar connection button click."""
        from ..sync.gcal_credentials import validate_credentials
        from ..sync.gcal_sync import GoogleCalendarSync
        import threading

        # Validate credentials first
        creds_valid, error_msg = validate_credentials()
        if not creds_valid:
            # Show error dialog
            dialog = Gtk.MessageDialog(
                parent=self,
                modal=True,
                destroy_with_parent=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="OAuth Credentials Not Configured"
            )
            dialog.format_secondary_text(error_msg)
            dialog.run()
            dialog.destroy()
            return

        button.set_sensitive(False)
        self.gcal_status_label.set_markup("<span color='blue'>Connecting...</span>")

        def connect():
            """Run OAuth flow in background thread."""
            try:
                # Create sync instance and trigger authentication
                gcal_ids = self.db.get_config('gcal_calendar_ids', DEFAULT_CALENDAR_IDS)
                gcal_sync = GoogleCalendarSync(self.db, gcal_ids)

                # This will trigger OAuth flow if needed
                if gcal_sync._authenticate():
                    # Mark as connected
                    self.db.set_config('gcal_connected', True)

                    # Update UI on main thread
                    from gi.repository import GLib
                    GLib.idle_add(self._on_calendar_connected, True)
                else:
                    from gi.repository import GLib
                    GLib.idle_add(self._on_calendar_connected, False)

            except Exception as e:
                import logging
                logging.error(f"Calendar connection error: {e}")
                from gi.repository import GLib
                GLib.idle_add(self._on_calendar_connected, False)

        # Run in background thread
        thread = threading.Thread(target=connect, daemon=True)
        thread.start()

    def _on_calendar_connected(self, success: bool):
        """Handle calendar connection result (called on main thread)."""
        if success:
            self.gcal_status_label.set_markup("<span color='green'>✓ Connected</span>")
        else:
            self.gcal_status_label.set_markup("<span color='red'>✗ Connection failed</span>")

        # Re-enable button
        for child in self.get_content_area().get_children():
            if isinstance(child, Gtk.Notebook):
                for page_num in range(child.get_n_pages()):
                    page = child.get_nth_page(page_num)
                    for widget in page.get_children():
                        if isinstance(widget, Gtk.Button):
                            widget.set_sensitive(True)

    def _on_test_github_clicked(self, button):
        """Handle GitHub test connection button click."""
        from ..sync.github_sync import GitHubSync
        import threading
        from gi.repository import GLib

        # Get current settings
        token = self.github_token_entry.get_text().strip()
        org = self.github_org_entry.get_text().strip()
        project = int(self.github_project_spin.get_value())

        if not token or not org:
            self.github_status_label.set_markup(
                "<small><span color='red'>Please enter token and organization</span></small>"
            )
            return

        # Disable button and show testing status
        button.set_sensitive(False)
        self.github_status_label.set_markup("<small><span color='blue'>⟳ Testing connection...</span></small>")

        def test():
            """Test GitHub connection in background thread."""
            try:
                github_sync = GitHubSync(self.db, token, org, project)
                # Try to fetch current iteration (lightweight test)
                iteration = github_sync._get_current_iteration()

                # If we got here without error, connection works
                GLib.idle_add(self._on_github_test_complete, True, f"Connected successfully! Current iteration: {iteration or 'None'}")
            except Exception as e:
                error_msg = str(e)
                GLib.idle_add(self._on_github_test_complete, False, error_msg)

        # Run in background thread
        thread = threading.Thread(target=test, daemon=True)
        thread.start()

    def _on_github_test_complete(self, success: bool, message: str):
        """Handle GitHub test completion (called on main thread).

        Args:
            success: Whether the test succeeded
            message: Result message
        """
        # Find and re-enable the test button
        for child in self.get_content_area().get_children():
            if isinstance(child, Gtk.Notebook):
                for page_num in range(child.get_n_pages()):
                    page = child.get_nth_page(page_num)
                    for widget in page.get_children():
                        if isinstance(widget, Gtk.Button) and widget.get_label() == "Test Connection":
                            widget.set_sensitive(True)

        # Update status label
        if success:
            self.github_status_label.set_markup(
                f"<small><span color='green'>✓ {message[:80]}</span></small>"
            )
        else:
            self.github_status_label.set_markup(
                f"<small><span color='red'>✗ Connection failed: {message[:80]}</span></small>"
            )

        return False

    def _on_create_backup_clicked(self, button):
        """Handle create backup button click."""
        button.set_sensitive(False)
        self.backup_status_label.set_markup("<small><span color='blue'>Creating backup...</span></small>")

        try:
            backup_path = self.db.create_backup(reason="manual")
            if backup_path:
                self.backup_status_label.set_markup(
                    f"<small><span color='green'>✓ Backup created: {backup_path}</span></small>"
                )
            else:
                self.backup_status_label.set_markup(
                    "<small><span color='red'>✗ Backup failed</span></small>"
                )
        except Exception as e:
            self.backup_status_label.set_markup(
                f"<small><span color='red'>✗ Error: {str(e)[:50]}</span></small>"
            )
        finally:
            button.set_sensitive(True)

    def _on_export_data_clicked(self, button):
        """Handle export data button click."""
        # Show file chooser dialog
        dialog = Gtk.FileChooserDialog(
            title="Export Data to JSON",
            parent=self,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Save", Gtk.ResponseType.OK)
        dialog.set_current_name("whatnow_export.json")

        response = dialog.run()
        export_path = dialog.get_filename()
        dialog.destroy()

        if response == Gtk.ResponseType.OK and export_path:
            button.set_sensitive(False)
            self.backup_status_label.set_markup("<small><span color='blue'>Exporting data...</span></small>")

            try:
                if self.db.export_data(export_path):
                    self.backup_status_label.set_markup(
                        f"<small><span color='green'>✓ Data exported: {export_path}</span></small>"
                    )
                else:
                    self.backup_status_label.set_markup(
                        "<small><span color='red'>✗ Export failed</span></small>"
                    )
            except Exception as e:
                self.backup_status_label.set_markup(
                    f"<small><span color='red'>✗ Error: {str(e)[:50]}</span></small>"
                )
            finally:
                button.set_sensitive(True)

    def run_and_save(self) -> bool:
        """Run the dialog and save settings if OK was clicked.

        Returns:
            True if settings were saved, False if cancelled
        """
        response = self.run()

        if response == Gtk.ResponseType.OK:
            self._save_settings()
            self.destroy()
            return True

        self.destroy()
        return False


def show_settings_dialog(parent: Optional[Gtk.Window], db) -> bool:
    """Show settings dialog.

    Args:
        parent: Parent window
        db: Database instance

    Returns:
        True if settings were saved, False if cancelled
    """
    dialog = SettingsDialog(parent, db)
    return dialog.run_and_save()
