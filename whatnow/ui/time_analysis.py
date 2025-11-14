"""Time analysis view for TagTime statistics."""

import gi

gi.require_version("Gtk", "3.0")
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from gi.repository import Gtk, Pango


class TimeAnalysisWidget(Gtk.Box):
    """Widget for analyzing time tracking data."""

    def __init__(self, db):
        """Initialize the time analysis widget.

        Args:
            db: Database instance
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_border_width(10)

        self.db = db

        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.pack_start(toolbar, False, False, 0)

        # Date range selector
        toolbar.pack_start(Gtk.Label(label="View:"), False, False, 0)

        self.range_combo = Gtk.ComboBoxText()
        self.range_combo.append_text("Today")
        self.range_combo.append_text("Yesterday")
        self.range_combo.append_text("This Week")
        self.range_combo.append_text("Last Week")
        self.range_combo.set_active(0)
        self.range_combo.connect("changed", self._on_range_changed)
        toolbar.pack_start(self.range_combo, False, False, 0)

        # Refresh button
        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.connect("clicked", lambda b: self._refresh_analysis())
        toolbar.pack_end(refresh_button, False, False, 0)

        # Create notebook for different views
        notebook = Gtk.Notebook()
        self.pack_start(notebook, True, True, 0)

        # Summary tab
        self.summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.summary_box.set_border_width(10)
        summary_label = Gtk.Label(label="Summary")
        notebook.append_page(self.summary_box, summary_label)

        # By Tag tab
        self.tags_box = self._create_analysis_tab()
        tags_label = Gtk.Label(label="By Tag")
        notebook.append_page(self.tags_box, tags_label)

        # By TODO tab
        self.todos_box = self._create_analysis_tab()
        todos_label = Gtk.Label(label="By TODO")
        notebook.append_page(self.todos_box, todos_label)

        # Load initial data
        self._refresh_analysis()

    def _create_analysis_tab(self) -> Gtk.Box:
        """Create a tab for analysis data.

        Returns:
            Box widget containing scrolled list
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(10)

        # Create list store: item, pings, percentage, hours
        store = Gtk.ListStore(str, int, str, str)

        # Create tree view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        tree_view = Gtk.TreeView(model=store)

        # Item column
        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Item", renderer, text=0)
        column.set_resizable(True)
        column.set_expand(True)
        tree_view.append_column(column)

        # Pings column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Pings", renderer, text=1)
        column.set_min_width(60)
        tree_view.append_column(column)

        # Percentage column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("%", renderer, text=2)
        column.set_min_width(60)
        tree_view.append_column(column)

        # Hours column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Time", renderer, text=3)
        column.set_min_width(80)
        tree_view.append_column(column)

        scrolled.add(tree_view)
        box.pack_start(scrolled, True, True, 0)

        # Store reference to the store and tree_view
        box.store = store
        box.tree_view = tree_view

        return box

    def _get_date_range(self) -> tuple:
        """Get the start and end timestamps for the selected range.

        Returns:
            Tuple of (start_timestamp, end_timestamp, description)
        """
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0)

        range_idx = self.range_combo.get_active()

        if range_idx == 0:  # Today
            start = today_start
            end = now
            desc = "Today"
        elif range_idx == 1:  # Yesterday
            start = today_start - timedelta(days=1)
            end = today_start - timedelta(seconds=1)
            desc = "Yesterday"
        elif range_idx == 2:  # This Week
            # Start of week (Monday)
            start = today_start - timedelta(days=now.weekday())
            end = now
            desc = "This Week"
        else:  # Last Week
            # Last Monday to Sunday
            start = today_start - timedelta(days=now.weekday() + 7)
            end = today_start - timedelta(days=now.weekday() + 1) - timedelta(seconds=1)
            desc = "Last Week"

        return (int(start.timestamp()), int(end.timestamp()), desc)

    def _refresh_analysis(self):
        """Refresh the analysis data."""
        start_ts, end_ts, desc = self._get_date_range()

        # Get pings for the date range
        pings = self.db.get_pings_by_date_range(start_ts, end_ts)

        # Get work sessions for the date range
        total_work_seconds = 0
        if desc == "Today":
            total_work_seconds = self.db.get_total_work_seconds_for_day(start_ts)
        else:
            # Calculate for each day in range
            current = datetime.fromtimestamp(start_ts)
            end_dt = datetime.fromtimestamp(end_ts)
            while current <= end_dt:
                total_work_seconds += self.db.get_total_work_seconds_for_day(
                    int(current.timestamp())
                )
                current += timedelta(days=1)

        total_work_hours = total_work_seconds / 3600.0

        # Update summary
        self._update_summary(desc, pings, total_work_hours)

        # Analyze by tags
        self._analyze_by_tags(pings, total_work_hours)

        # Analyze by TODOs
        self._analyze_by_todos(pings, total_work_hours)

    def _update_summary(self, period: str, pings: List[Dict], total_hours: float):
        """Update the summary tab.

        Args:
            period: Period description
            pings: List of pings
            total_hours: Total working hours
        """
        # Clear existing content
        for child in self.summary_box.get_children():
            self.summary_box.remove(child)

        # Create summary content
        title = Gtk.Label()
        title.set_markup(f"<big><b>{period} Summary</b></big>")
        self.summary_box.pack_start(title, False, False, 10)

        # Stats grid
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(20)
        grid.set_halign(Gtk.Align.CENTER)

        row = 0

        # Total working hours
        label = Gtk.Label(label="Total Working Hours:", xalign=0)
        label.set_markup("<b>Total Working Hours:</b>")
        grid.attach(label, 0, row, 1, 1)
        value = Gtk.Label(label=f"{total_hours:.1f}h", xalign=0)
        grid.attach(value, 1, row, 1, 1)
        row += 1

        # Total pings
        label = Gtk.Label(label="Total Pings:", xalign=0)
        label.set_markup("<b>Total Pings:</b>")
        grid.attach(label, 0, row, 1, 1)
        value = Gtk.Label(label=str(len(pings)), xalign=0)
        grid.attach(value, 1, row, 1, 1)
        row += 1

        # Meeting pings
        meeting_pings = sum(1 for p in pings if p.get("is_meeting"))
        label = Gtk.Label(label="Meeting Pings:", xalign=0)
        label.set_markup("<b>Meeting Pings:</b>")
        grid.attach(label, 0, row, 1, 1)
        value = Gtk.Label(label=str(meeting_pings), xalign=0)
        grid.attach(value, 1, row, 1, 1)
        row += 1

        # Work pings (non-meeting)
        work_pings = len(pings) - meeting_pings
        label = Gtk.Label(label="Work Pings:", xalign=0)
        label.set_markup("<b>Work Pings:</b>")
        grid.attach(label, 0, row, 1, 1)
        value = Gtk.Label(label=str(work_pings), xalign=0)
        grid.attach(value, 1, row, 1, 1)
        row += 1

        if len(pings) > 0 and total_hours > 0:
            # Average time per ping
            avg_hours = total_hours / len(pings)
            label = Gtk.Label(label="Avg. Time per Ping:", xalign=0)
            label.set_markup("<b>Avg. Time per Ping:</b>")
            grid.attach(label, 0, row, 1, 1)
            value = Gtk.Label(label=f"{avg_hours * 60:.1f} min", xalign=0)
            grid.attach(value, 1, row, 1, 1)
            row += 1

        self.summary_box.pack_start(grid, False, False, 10)

        # Explanation
        explanation = Gtk.Label()
        explanation.set_markup(
            "<small><i>TagTime uses statistical sampling: the fraction of pings\n"
            "for each activity approximates the fraction of time spent on it.</i></small>"
        )
        explanation.set_line_wrap(True)
        self.summary_box.pack_start(explanation, False, False, 10)

        self.summary_box.show_all()

    def _analyze_by_tags(self, pings: List[Dict], total_hours: float):
        """Analyze pings by tags.

        Args:
            pings: List of pings
            total_hours: Total working hours
        """
        self.tags_box.store.clear()

        if not pings:
            return

        # Count pings per tag
        tag_counts: defaultdict[str, int] = defaultdict(int)
        for ping in pings:
            tags = ping.get("tags", [])
            if tags:
                for tag in tags:
                    tag_counts[tag] += 1

        # Calculate percentages and hours
        total_pings = len(pings)

        # Sort by count descending
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

        for tag, count in sorted_tags:
            percentage = (count / total_pings) * 100
            hours = (count / total_pings) * total_hours

            self.tags_box.store.append([tag, count, f"{percentage:.1f}%", f"{hours:.1f}h"])

    def _analyze_by_todos(self, pings: List[Dict], total_hours: float):
        """Analyze pings by TODOs.

        Args:
            pings: List of pings
            total_hours: Total working hours
        """
        self.todos_box.store.clear()

        if not pings:
            return

        # Count pings per TODO
        todo_counts: defaultdict[str, int] = defaultdict(int)
        todo_names: dict[str, str] = {}

        for ping in pings:
            todo_id = ping.get("todo_id")
            todo_type = ping.get("todo_type")

            if not todo_id:
                continue

            if todo_type == "meeting":
                # Get event summary from notes or event ID
                name = ping.get("notes", "Meeting")
            elif todo_type == "github":
                # Get GitHub task title
                task = self.db.get_github_tasks()
                task_match = next((t for t in task if t["id"] == todo_id), None)
                name = task_match["title"] if task_match else f"GitHub Task {todo_id}"
            elif todo_type == "local":
                # Get local TODO text
                try:
                    todo = self.db.get_local_todo(int(todo_id))
                    name = todo["text"] if todo else f"Local TODO {todo_id}"
                except:
                    name = f"Local TODO {todo_id}"
            else:
                name = f"{todo_type} {todo_id}"

            key = f"{todo_type}:{todo_id}"
            todo_counts[key] += 1
            todo_names[key] = name

        # Calculate percentages and hours
        total_pings = len(pings)

        # Sort by count descending
        sorted_todos = sorted(todo_counts.items(), key=lambda x: x[1], reverse=True)

        for key, count in sorted_todos:
            name = todo_names.get(key, key)
            percentage = (count / total_pings) * 100
            hours = (count / total_pings) * total_hours

            self.todos_box.store.append([name, count, f"{percentage:.1f}%", f"{hours:.1f}h"])

    def _on_range_changed(self, combo):
        """Handle range change."""
        self._refresh_analysis()

    def refresh(self):
        """Public method to refresh the analysis."""
        self._refresh_analysis()
