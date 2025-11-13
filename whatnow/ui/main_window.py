"""Main GTK application window."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable

from .todo_management import TodoManagementWidget
from .time_analysis import TimeAnalysisWidget


class MainWindow(Gtk.ApplicationWindow):
    """Main application window showing activity history."""

    def __init__(self, app: Gtk.Application, db, on_settings_click: Optional[Callable] = None):
        """Initialize the main window.

        Args:
            app: GTK application
            db: Database instance
            on_settings_click: Callback for settings button
        """
        super().__init__(application=app, title="WhatNow - Activity Tracker")

        self.db = db
        self.on_settings_click = on_settings_click

        # Pagination state for pings
        self.current_page = 0
        self.page_size = 100

        # Set window properties
        self.set_default_size(800, 600)
        self.set_border_width(0)

        # Create main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)

        # Create header bar
        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.set_title("WhatNow")
        header_bar.set_subtitle("Activity Tracker")

        # Add settings button to header
        settings_button = Gtk.Button()
        settings_icon = Gtk.Image.new_from_icon_name("preferences-system", Gtk.IconSize.BUTTON)
        settings_button.add(settings_icon)
        settings_button.set_tooltip_text("Settings")
        settings_button.connect("clicked", self._on_settings_clicked)
        header_bar.pack_end(settings_button)

        # Add refresh button
        refresh_button = Gtk.Button()
        refresh_icon = Gtk.Image.new_from_icon_name("view-refresh", Gtk.IconSize.BUTTON)
        refresh_button.add(refresh_icon)
        refresh_button.set_tooltip_text("Refresh")
        refresh_button.connect("clicked", self._on_refresh_clicked)
        header_bar.pack_end(refresh_button)

        self.set_titlebar(header_bar)

        # Create notebook for different views
        self.notebook = Gtk.Notebook()
        vbox.pack_start(self.notebook, True, True, 0)

        # Create status bar
        self.statusbar = Gtk.Statusbar()
        self.statusbar.set_margin_start(6)
        self.statusbar.set_margin_end(6)
        self.statusbar.set_margin_top(3)
        self.statusbar.set_margin_bottom(3)
        self.status_context_id = self.statusbar.get_context_id("main")
        vbox.pack_start(self.statusbar, False, False, 0)

        # Create pings view
        self._create_pings_view()

        # Create tasks view
        self._create_tasks_view()

        # Create calendar view
        self._create_calendar_view()

        # Create TODO management view
        self.todo_widget = TodoManagementWidget(db)
        todo_label = Gtk.Label(label="My TODOs")
        self.notebook.append_page(self.todo_widget, todo_label)

        # Create time analysis view
        self.time_analysis_widget = TimeAnalysisWidget(db)
        analysis_label = Gtk.Label(label="Time Analysis")
        self.notebook.append_page(self.time_analysis_widget, analysis_label)

        # Set up keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Show all widgets
        self.show_all()

        # Load initial data
        self._refresh_pings()

    def _create_pings_view(self):
        """Create the pings history view."""
        # Container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_border_width(10)

        # Create list store: timestamp, activity, tags, notes, id
        self.pings_store = Gtk.ListStore(str, str, str, str, int)

        # Create tree view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.pings_view = Gtk.TreeView(model=self.pings_store)
        self.pings_view.set_enable_search(True)
        self.pings_view.set_search_column(1)

        # Timestamp column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Time", renderer, text=0)
        column.set_sort_column_id(0)
        column.set_resizable(True)
        column.set_min_width(150)
        self.pings_view.append_column(column)

        # Activity column
        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Activity", renderer, text=1)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        column.set_expand(True)
        self.pings_view.append_column(column)

        # Tags column
        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Tags", renderer, text=2)
        column.set_sort_column_id(2)
        column.set_resizable(True)
        column.set_min_width(150)
        self.pings_view.append_column(column)

        scrolled.add(self.pings_view)
        vbox.pack_start(scrolled, True, True, 0)

        # Pagination controls
        pagination_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        pagination_box.set_halign(Gtk.Align.CENTER)

        self.prev_button = Gtk.Button(label="◀ Previous")
        self.prev_button.connect("clicked", self._on_prev_page_clicked)
        pagination_box.pack_start(self.prev_button, False, False, 0)

        self.page_label = Gtk.Label()
        self.page_label.set_markup("<b>Page 1 of 1</b>")
        pagination_box.pack_start(self.page_label, False, False, 10)

        self.next_button = Gtk.Button(label="Next ▶")
        self.next_button.connect("clicked", self._on_next_page_clicked)
        pagination_box.pack_start(self.next_button, False, False, 0)

        vbox.pack_start(pagination_box, False, False, 6)

        # Info label
        self.pings_info_label = Gtk.Label()
        self.pings_info_label.set_markup("<small>Loading pings...</small>")
        self.pings_info_label.set_halign(Gtk.Align.START)
        vbox.pack_start(self.pings_info_label, False, False, 0)

        # Add to notebook
        label = Gtk.Label(label="Activity Pings")
        self.notebook.append_page(vbox, label)

    def _create_tasks_view(self):
        """Create the GitHub tasks view."""
        # Container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_border_width(10)

        # Create list store: title, state, iteration, url, id
        self.tasks_store = Gtk.ListStore(str, str, str, str, str)

        # Create tree view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        tasks_view = Gtk.TreeView(model=self.tasks_store)
        tasks_view.set_enable_search(True)
        tasks_view.set_search_column(0)

        # Title column
        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Task", renderer, text=0)
        column.set_resizable(True)
        column.set_expand(True)
        tasks_view.append_column(column)

        # State column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("State", renderer, text=1)
        column.set_resizable(True)
        tasks_view.append_column(column)

        # Iteration column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Iteration", renderer, text=2)
        column.set_resizable(True)
        tasks_view.append_column(column)

        scrolled.add(tasks_view)
        vbox.pack_start(scrolled, True, True, 0)

        # Info label
        self.tasks_info_label = Gtk.Label()
        self.tasks_info_label.set_markup("<small>No GitHub tasks synced yet</small>")
        self.tasks_info_label.set_halign(Gtk.Align.START)
        vbox.pack_start(self.tasks_info_label, False, False, 0)

        # Add to notebook
        label = Gtk.Label(label="GitHub Tasks")
        self.notebook.append_page(vbox, label)

    def _create_calendar_view(self):
        """Create the calendar events view."""
        # Container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_border_width(10)

        # Create list store: time, summary, location, id
        self.events_store = Gtk.ListStore(str, str, str, str)

        # Create tree view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        events_view = Gtk.TreeView(model=self.events_store)
        events_view.set_enable_search(True)
        events_view.set_search_column(1)

        # Time column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Time", renderer, text=0)
        column.set_resizable(True)
        column.set_min_width(150)
        events_view.append_column(column)

        # Summary column
        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Event", renderer, text=1)
        column.set_resizable(True)
        column.set_expand(True)
        events_view.append_column(column)

        # Location column
        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Location", renderer, text=2)
        column.set_resizable(True)
        events_view.append_column(column)

        scrolled.add(events_view)
        vbox.pack_start(scrolled, True, True, 0)

        # Info label
        self.events_info_label = Gtk.Label()
        self.events_info_label.set_markup("<small>No calendar events synced yet</small>")
        self.events_info_label.set_halign(Gtk.Align.START)
        vbox.pack_start(self.events_info_label, False, False, 0)

        # Add to notebook
        label = Gtk.Label(label="Calendar")
        self.notebook.append_page(vbox, label)

    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for the application."""
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)

        # Ctrl+R: Refresh
        refresh_key, refresh_mod = Gtk.accelerator_parse("<Control>r")
        accel_group.connect(
            refresh_key,
            refresh_mod,
            Gtk.AccelFlags.VISIBLE,
            lambda *args: self._on_refresh_clicked(None)
        )

        # Ctrl+comma: Settings
        settings_key, settings_mod = Gtk.accelerator_parse("<Control>comma")
        accel_group.connect(
            settings_key,
            settings_mod,
            Gtk.AccelFlags.VISIBLE,
            lambda *args: self._on_settings_clicked(None)
        )

        # Ctrl+N: New TODO (switch to TODO tab)
        new_todo_key, new_todo_mod = Gtk.accelerator_parse("<Control>n")
        accel_group.connect(
            new_todo_key,
            new_todo_mod,
            Gtk.AccelFlags.VISIBLE,
            self._on_new_todo_shortcut
        )

    def _on_new_todo_shortcut(self, *args):
        """Handle Ctrl+N keyboard shortcut to create new TODO."""
        # Switch to TODO management tab (index 3)
        self.notebook.set_current_page(3)
        # Trigger the add TODO dialog
        if hasattr(self.todo_widget, '_on_add_clicked'):
            self.todo_widget._on_add_clicked(None)
        return True

    def _refresh_pings(self):
        """Refresh the pings list."""
        try:
            # Get total count
            total_pings = self.db.count_pings()
            total_pages = max(1, (total_pings + self.page_size - 1) // self.page_size)

            # Ensure current page is valid
            if self.current_page >= total_pages:
                self.current_page = max(0, total_pages - 1)

            # Calculate offset
            offset = self.current_page * self.page_size

            # Fetch pings for current page
            pings = self.db.get_pings(limit=self.page_size, offset=offset)
            self.pings_store.clear()

            for ping in pings:
                dt = datetime.fromtimestamp(ping['timestamp'])
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                tags_str = ', '.join(ping.get('tags', []))

                self.pings_store.append([
                    time_str,
                    ping['activity'],
                    tags_str,
                    ping.get('notes', ''),
                    ping['id']
                ])

            # Update pagination controls
            self.page_label.set_markup(f"<b>Page {self.current_page + 1} of {total_pages}</b>")
            self.prev_button.set_sensitive(self.current_page > 0)
            self.next_button.set_sensitive(self.current_page < total_pages - 1)

            # Update info label
            start_idx = offset + 1
            end_idx = min(offset + len(pings), total_pings)
            self.pings_info_label.set_markup(
                f"<small>Showing {start_idx}-{end_idx} of {total_pings} pings</small>"
            )
        except Exception as e:
            self.pings_info_label.set_markup(
                f"<small>Error loading pings: {e}</small>"
            )

    def refresh_tasks(self):
        """Refresh the tasks list."""
        try:
            tasks = self.db.get_github_tasks()
            self.tasks_store.clear()

            for task in tasks:
                self.tasks_store.append([
                    task['title'],
                    task['state'],
                    task.get('iteration', ''),
                    task.get('url', ''),
                    task['id']
                ])

            self.tasks_info_label.set_markup(
                f"<small>Showing {len(tasks)} tasks</small>"
            )
        except Exception as e:
            self.tasks_info_label.set_markup(
                f"<small>Error loading tasks: {e}</small>"
            )

    def refresh_events(self):
        """Refresh the calendar events list."""
        try:
            # Get events for next 7 days
            now = int(datetime.now().timestamp())
            week_later = now + (7 * 24 * 60 * 60)

            events = self.db.get_calendar_events(now, week_later)
            self.events_store.clear()

            for event in events:
                dt = datetime.fromtimestamp(event['start_time'])
                time_str = dt.strftime('%Y-%m-%d %H:%M')

                self.events_store.append([
                    time_str,
                    event['summary'],
                    event.get('location', ''),
                    event['id']
                ])

            self.events_info_label.set_markup(
                f"<small>Showing {len(events)} upcoming events</small>"
            )
        except Exception as e:
            self.events_info_label.set_markup(
                f"<small>Error loading events: {e}</small>"
            )

    def _on_prev_page_clicked(self, button):
        """Handle previous page button click."""
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_pings()

    def _on_next_page_clicked(self, button):
        """Handle next page button click."""
        total_pings = self.db.count_pings()
        total_pages = max(1, (total_pings + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._refresh_pings()

    def _on_settings_clicked(self, button):
        """Handle settings button click."""
        if self.on_settings_click:
            self.on_settings_click()

    def _on_refresh_clicked(self, button):
        """Handle refresh button click."""
        self.show_loading("Refreshing...")
        self.current_page = 0  # Reset to first page on refresh
        self._refresh_pings()
        self.refresh_tasks()
        self.refresh_events()
        self.set_status("Refreshed successfully")
        # Clear status after 3 seconds
        GLib.timeout_add_seconds(3, self.clear_status)

    def refresh_all(self):
        """Refresh all views."""
        self.current_page = 0  # Reset to first page on refresh
        self._refresh_pings()
        self.refresh_tasks()
        self.refresh_events()
        if hasattr(self, 'todo_widget'):
            self.todo_widget.refresh()
        if hasattr(self, 'time_analysis_widget'):
            self.time_analysis_widget.refresh()

    def set_status(self, message: str):
        """Set status bar message.

        Args:
            message: Status message to display
        """
        self.statusbar.pop(self.status_context_id)
        self.statusbar.push(self.status_context_id, message)

    def clear_status(self):
        """Clear status bar message."""
        self.statusbar.pop(self.status_context_id)

    def show_loading(self, message: str = "Loading..."):
        """Show loading indicator in status bar.

        Args:
            message: Loading message to display
        """
        self.set_status(f"⟳ {message}")

    def hide_loading(self):
        """Hide loading indicator."""
        self.clear_status()
