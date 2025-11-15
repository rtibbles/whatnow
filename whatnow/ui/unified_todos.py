"""Unified TODO view combining GitHub tasks and local TODOs."""

import gi

gi.require_version("Gtk", "3.0")
from typing import Any, Dict, List, Optional

from gi.repository import Gtk, Pango


class UnifiedTodosWidget(Gtk.Box):
    """Widget showing all TODOs (GitHub + local) in priority order."""

    # Priority labels mapping
    URGENCY_LABELS = {1: "Low", 2: "Medium", 3: "High", 4: "Urgent"}
    IMPORTANCE_LABELS = {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}

    def __init__(self, db):
        """Initialize the unified TODOs widget.

        Args:
            db: Database instance
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_border_width(10)

        self.db = db

        # Create toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_bottom(6)

        # Add local TODO button
        add_button = Gtk.Button(label="New Local TODO")
        add_button.connect("clicked", self._on_add_todo_clicked)
        toolbar.pack_start(add_button, False, False, 0)

        # Refresh button
        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.connect("clicked", self._on_refresh_clicked)
        toolbar.pack_start(refresh_button, False, False, 0)

        # Filter dropdown
        filter_label = Gtk.Label(label="Show:")
        filter_label.set_margin_start(12)
        toolbar.pack_start(filter_label, False, False, 0)

        self.filter_combo = Gtk.ComboBoxText()
        self.filter_combo.append_text("All TODOs")
        self.filter_combo.append_text("GitHub Only")
        self.filter_combo.append_text("Local Only")
        self.filter_combo.set_active(0)
        self.filter_combo.connect("changed", self._on_filter_changed)
        toolbar.pack_start(self.filter_combo, False, False, 0)

        self.pack_start(toolbar, False, False, 0)

        # Create list store: priority_score, source, title, urgency, importance, id, type
        self.todos_store = Gtk.ListStore(int, str, str, str, str, str, str)

        # Create tree view with scrolling
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.todos_view = Gtk.TreeView(model=self.todos_store)
        self.todos_view.set_enable_search(True)
        self.todos_view.set_search_column(2)  # Search by title
        self.todos_view.connect("row-activated", self._on_row_activated)

        # Priority Score column
        renderer = Gtk.CellRendererText()
        renderer.set_property("weight", 700)  # Bold
        column = Gtk.TreeViewColumn("Priority", renderer, text=0)
        column.set_resizable(True)
        column.set_min_width(70)
        column.set_sort_column_id(0)
        self.todos_view.append_column(column)

        # Source column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Source", renderer, text=1)
        column.set_resizable(True)
        column.set_min_width(80)
        self.todos_view.append_column(column)

        # Title column
        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Title", renderer, text=2)
        column.set_resizable(True)
        column.set_expand(True)
        column.set_min_width(200)
        self.todos_view.append_column(column)

        # Urgency column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Urgency", renderer, text=3)
        column.set_resizable(True)
        column.set_min_width(80)
        self.todos_view.append_column(column)

        # Importance column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Importance", renderer, text=4)
        column.set_resizable(True)
        column.set_min_width(80)
        self.todos_view.append_column(column)

        scrolled.add(self.todos_view)
        self.pack_start(scrolled, True, True, 0)

        # Info label
        self.info_label = Gtk.Label()
        self.info_label.set_markup("<small>Loading TODOs...</small>")
        self.info_label.set_halign(Gtk.Align.START)
        self.pack_start(self.info_label, False, False, 0)

        # Context menu
        self._create_context_menu()

        # Connect right-click
        self.todos_view.connect("button-press-event", self._on_button_press)

        # Initial load
        self.refresh()

    def _create_context_menu(self):
        """Create right-click context menu."""
        self.context_menu = Gtk.Menu()

        # Edit item
        edit_item = Gtk.MenuItem(label="Edit")
        edit_item.connect("activate", self._on_edit_clicked)
        self.context_menu.append(edit_item)

        # Complete item
        complete_item = Gtk.MenuItem(label="Mark Complete")
        complete_item.connect("activate", self._on_complete_clicked)
        self.context_menu.append(complete_item)

        # Open in browser (GitHub only)
        self.open_item = Gtk.MenuItem(label="Open in GitHub")
        self.open_item.connect("activate", self._on_open_github_clicked)
        self.context_menu.append(self.open_item)

        self.context_menu.show_all()

    def _on_button_press(self, widget, event):
        """Handle button press for context menu."""
        if event.button == 3:  # Right click
            path = self.todos_view.get_path_at_pos(int(event.x), int(event.y))
            if path:
                self.todos_view.get_selection().select_path(path[0])

                # Get selected item type
                model, treeiter = self.todos_view.get_selection().get_selected()
                if treeiter:
                    item_type = model.get_value(treeiter, 6)
                    # Show/hide GitHub-specific menu item
                    self.open_item.set_visible(item_type == "github")

                self.context_menu.popup_at_pointer(event)
            return True
        return False

    def refresh(self):
        """Refresh the TODOs list."""
        self.todos_store.clear()

        # Get filter selection
        filter_option = self.filter_combo.get_active()

        all_todos: List[Dict[str, Any]] = []

        # Get GitHub tasks (only active ones - not DONE)
        if filter_option in [0, 1]:  # All or GitHub only
            github_tasks = self.db.get_github_tasks()
            for task in github_tasks:
                if task["state"] in ["OPEN", "IN_PROGRESS", "TODO"]:
                    urgency = task.get("urgency") or 2
                    importance = task.get("importance") or 2
                    priority_score = urgency * importance

                    all_todos.append(
                        {
                            "priority_score": priority_score,
                            "source": "GitHub",
                            "title": task["title"],
                            "urgency": self.URGENCY_LABELS.get(urgency, "Medium"),
                            "importance": self.IMPORTANCE_LABELS.get(importance, "Medium"),
                            "id": task["id"],
                            "type": "github",
                            "url": task.get("url"),
                        }
                    )

        # Get local TODOs (only active)
        if filter_option in [0, 2]:  # All or Local only
            local_todos = self.db.get_local_todos(active_only=True)
            for todo in local_todos:
                urgency = todo.get("urgency", 2)
                importance = todo.get("importance", 2)
                priority_score = urgency * importance

                all_todos.append(
                    {
                        "priority_score": priority_score,
                        "source": "Local",
                        "title": todo["text"],
                        "urgency": self.URGENCY_LABELS.get(urgency, "Medium"),
                        "importance": self.IMPORTANCE_LABELS.get(importance, "Medium"),
                        "id": str(todo["id"]),
                        "type": "local",
                        "url": None,
                    }
                )

        # Sort by priority score (highest first)
        all_todos.sort(key=lambda x: x["priority_score"], reverse=True)

        # Populate list store
        for todo in all_todos:
            self.todos_store.append(
                [
                    todo["priority_score"],
                    todo["source"],
                    todo["title"],
                    todo["urgency"],
                    todo["importance"],
                    todo["id"],
                    todo["type"],
                ]
            )

        # Update info label
        github_count = sum(1 for t in all_todos if t["type"] == "github")
        local_count = sum(1 for t in all_todos if t["type"] == "local")

        if all_todos:
            self.info_label.set_markup(
                f"<small>Showing {len(all_todos)} TODOs: "
                f"{github_count} from GitHub, {local_count} local</small>"
            )
        else:
            self.info_label.set_markup("<small>No active TODOs. Add one to get started!</small>")

    def _on_refresh_clicked(self, button):
        """Handle refresh button click."""
        self.refresh()

    def _on_filter_changed(self, combo):
        """Handle filter combo change."""
        self.refresh()

    def _on_add_todo_clicked(self, button):
        """Handle add TODO button click."""
        from .todo_management import AddTodoDialog

        dialog = AddTodoDialog(self.get_toplevel())
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            data = dialog.get_todo_data()
            if data:
                text, tags, urgency, importance = data
                self.db.add_local_todo(text, tags, urgency, importance)
                self.refresh()

        dialog.destroy()

    def _on_row_activated(self, treeview, path, column):
        """Handle double-click on row."""
        model = treeview.get_model()
        treeiter = model.get_iter(path)

        item_id = model.get_value(treeiter, 5)
        item_type = model.get_value(treeiter, 6)

        if item_type == "local":
            # Edit local TODO
            self._edit_local_todo(int(item_id))
        elif item_type == "github":
            # Open GitHub URL in browser
            self._open_github_url(item_id)

    def _on_edit_clicked(self, menu_item):
        """Handle edit menu item."""
        model, treeiter = self.todos_view.get_selection().get_selected()
        if not treeiter:
            return

        item_id = model.get_value(treeiter, 5)
        item_type = model.get_value(treeiter, 6)

        if item_type == "local":
            self._edit_local_todo(int(item_id))

    def _on_complete_clicked(self, menu_item):
        """Handle complete menu item."""
        model, treeiter = self.todos_view.get_selection().get_selected()
        if not treeiter:
            return

        item_id = model.get_value(treeiter, 5)
        item_type = model.get_value(treeiter, 6)

        if item_type == "local":
            # Complete local TODO
            self.db.complete_local_todo(int(item_id))
            self.refresh()
        # Note: GitHub tasks are synced from GitHub, can't mark complete here

    def _on_open_github_clicked(self, menu_item):
        """Handle open in GitHub menu item."""
        model, treeiter = self.todos_view.get_selection().get_selected()
        if not treeiter:
            return

        item_id = model.get_value(treeiter, 5)
        self._open_github_url(item_id)

    def _edit_local_todo(self, todo_id: int):
        """Open edit dialog for local TODO."""
        from .todo_management import TodoEditDialog

        todo = self.db.get_local_todo(todo_id)
        if not todo:
            return

        dialog = EditTodoDialog(self.get_toplevel(), todo)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            data = dialog.get_todo_data()
            if data:
                text, tags, urgency, importance = data
                self.db.update_local_todo(
                    todo_id, text=text, tags=tags, urgency=urgency, importance=importance
                )
                self.refresh()

        dialog.destroy()

    def _open_github_url(self, task_id: str):
        """Open GitHub task URL in browser."""
        task = self.db.get_github_task_by_id(task_id)
        if task and task.get("url"):
            import webbrowser

            webbrowser.open(task["url"])
