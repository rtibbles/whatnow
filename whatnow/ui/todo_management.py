"""Local TODO management UI."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango
from datetime import datetime
from typing import Optional, Callable


class TodoManagementWidget(Gtk.Box):
    """Widget for managing local TODOs."""

    def __init__(self, db, on_refresh: Optional[Callable] = None):
        """Initialize the TODO management widget.

        Args:
            db: Database instance
            on_refresh: Optional callback when TODOs are modified
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_border_width(10)

        self.db = db
        self.on_refresh = on_refresh

        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.pack_start(toolbar, False, False, 0)

        # Add TODO button
        add_button = Gtk.Button(label="Add TODO")
        add_button.connect("clicked", self._on_add_clicked)
        toolbar.pack_start(add_button, False, False, 0)

        # Edit button
        self.edit_button = Gtk.Button(label="Edit")
        self.edit_button.set_sensitive(False)
        self.edit_button.connect("clicked", self._on_edit_clicked)
        toolbar.pack_start(self.edit_button, False, False, 0)

        # Complete/Reactivate button
        self.toggle_button = Gtk.Button(label="Mark Complete")
        self.toggle_button.set_sensitive(False)
        self.toggle_button.connect("clicked", self._on_toggle_clicked)
        toolbar.pack_start(self.toggle_button, False, False, 0)

        # Filter dropdown
        toolbar.pack_start(Gtk.Label(label="Show:"), False, False, 10)
        self.filter_combo = Gtk.ComboBoxText()
        self.filter_combo.append_text("Active")
        self.filter_combo.append_text("Completed")
        self.filter_combo.append_text("All")
        self.filter_combo.set_active(0)
        self.filter_combo.connect("changed", self._on_filter_changed)
        toolbar.pack_start(self.filter_combo, False, False, 0)

        # Refresh button
        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.connect("clicked", lambda b: self._refresh_todos())
        toolbar.pack_end(refresh_button, False, False, 0)

        # Create list store: id, text, tags, is_active, created_at
        self.store = Gtk.ListStore(int, str, str, bool, str)

        # Create tree view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.tree_view = Gtk.TreeView(model=self.store)
        self.tree_view.set_enable_search(True)
        self.tree_view.set_search_column(1)

        # Selection
        self.selection = self.tree_view.get_selection()
        self.selection.connect("changed", self._on_selection_changed)

        # Status column (checkbox icon)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Status", renderer)
        column.set_cell_data_func(renderer, self._render_status)
        column.set_min_width(60)
        self.tree_view.append_column(column)

        # TODO text column
        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("TODO", renderer, text=1)
        column.set_resizable(True)
        column.set_expand(True)
        self.tree_view.append_column(column)

        # Tags column
        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Tags", renderer, text=2)
        column.set_resizable(True)
        column.set_min_width(150)
        self.tree_view.append_column(column)

        # Created date column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Created", renderer, text=4)
        column.set_resizable(True)
        column.set_min_width(120)
        self.tree_view.append_column(column)

        scrolled.add(self.tree_view)
        self.pack_start(scrolled, True, True, 0)

        # Info label
        self.info_label = Gtk.Label()
        self.info_label.set_markup("<small>Loading TODOs...</small>")
        self.info_label.set_halign(Gtk.Align.START)
        self.pack_start(self.info_label, False, False, 0)

        # Load initial data
        self._refresh_todos()

    def _render_status(self, column, cell, model, iter, data):
        """Render the status cell.

        Args:
            column: Tree view column
            cell: Cell renderer
            model: Tree model
            iter: Tree iter
            data: User data
        """
        is_active = model.get_value(iter, 3)
        if is_active:
            cell.set_property("text", "☐")
        else:
            cell.set_property("text", "☑")

    def _refresh_todos(self):
        """Refresh the TODO list."""
        filter_mode = self.filter_combo.get_active()

        # Get TODOs based on filter
        if filter_mode == 0:  # Active
            todos = self.db.get_local_todos(active_only=True)
        elif filter_mode == 1:  # Completed
            todos = self.db.get_local_todos(active_only=False)
            todos = [t for t in todos if not t['is_active']]
        else:  # All
            todos = self.db.get_local_todos(active_only=False)

        self.store.clear()

        for todo in todos:
            created_dt = datetime.fromtimestamp(todo['created_at'])
            created_str = created_dt.strftime('%Y-%m-%d %H:%M')
            tags_str = ', '.join(todo.get('tags', []))

            self.store.append([
                todo['id'],
                todo['text'],
                tags_str,
                todo['is_active'],
                created_str
            ])

        # Update info label
        active_count = sum(1 for t in todos if t['is_active'])
        completed_count = len(todos) - active_count
        self.info_label.set_markup(
            f"<small>Showing {len(todos)} TODOs "
            f"({active_count} active, {completed_count} completed)</small>"
        )

    def _on_selection_changed(self, selection):
        """Handle selection change."""
        model, iter = selection.get_selected()
        has_selection = iter is not None

        self.edit_button.set_sensitive(has_selection)
        self.toggle_button.set_sensitive(has_selection)

        if has_selection:
            is_active = model.get_value(iter, 3)
            if is_active:
                self.toggle_button.set_label("Mark Complete")
            else:
                self.toggle_button.set_label("Reactivate")

    def _on_add_clicked(self, button):
        """Handle add button click."""
        dialog = AddTodoDialog(self.get_toplevel())
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            data = dialog.get_todo_data()
            if data:
                text, tags = data
                self.db.add_local_todo(text, tags)
                self._refresh_todos()
                if self.on_refresh:
                    self.on_refresh()

        dialog.destroy()

    def _on_edit_clicked(self, button):
        """Handle edit button click."""
        model, iter = self.selection.get_selected()
        if not iter:
            return

        todo_id = model.get_value(iter, 0)
        todo = self.db.get_local_todo(todo_id)

        if todo:
            dialog = EditTodoDialog(self.get_toplevel(), todo)
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                data = dialog.get_todo_data()
                if data:
                    text, tags = data
                    self.db.update_local_todo(todo_id, text=text, tags=tags)
                    self._refresh_todos()
                    if self.on_refresh:
                        self.on_refresh()

            dialog.destroy()

    def _on_toggle_clicked(self, button):
        """Handle toggle button click."""
        model, iter = self.selection.get_selected()
        if not iter:
            return

        todo_id = model.get_value(iter, 0)
        todo_text = model.get_value(iter, 1)
        is_active = model.get_value(iter, 3)

        if is_active:
            # Confirm before completing
            dialog = Gtk.MessageDialog(
                parent=self.get_toplevel(),
                flags=Gtk.DialogFlags.MODAL,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Mark TODO as Complete?"
            )
            dialog.format_secondary_text(
                f"Are you sure you want to mark this TODO as complete?\n\n\"{todo_text}\"\n\n"
                "You can reactivate it later if needed."
            )
            response = dialog.run()
            dialog.destroy()

            if response != Gtk.ResponseType.YES:
                return

            self.db.complete_local_todo(todo_id)
        else:
            self.db.activate_local_todo(todo_id)

        self._refresh_todos()
        if self.on_refresh:
            self.on_refresh()

    def _on_filter_changed(self, combo):
        """Handle filter change."""
        self._refresh_todos()

    def refresh(self):
        """Public method to refresh the TODO list."""
        self._refresh_todos()


class AddTodoDialog(Gtk.Dialog):
    """Dialog to add a new TODO."""

    def __init__(self, parent: Optional[Gtk.Window]):
        """Initialize the add TODO dialog.

        Args:
            parent: Parent window
        """
        super().__init__(
            title="Add TODO",
            parent=parent,
            modal=True,
            destroy_with_parent=True
        )

        self.set_default_size(500, 200)
        self.set_border_width(10)

        # Add buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Add", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        # Create content
        content_area = self.get_content_area()
        content_area.set_spacing(10)

        # TODO text
        label = Gtk.Label(label="TODO:", xalign=0)
        content_area.pack_start(label, False, False, 0)

        self.text_entry = Gtk.Entry()
        self.text_entry.set_placeholder_text("What needs to be done?")
        self.text_entry.set_activates_default(True)
        content_area.pack_start(self.text_entry, False, False, 0)

        # Tags
        tags_label = Gtk.Label(label="Tags (space-separated):", xalign=0)
        content_area.pack_start(tags_label, False, False, 0)

        self.tags_entry = Gtk.Entry()
        self.tags_entry.set_placeholder_text("e.g., backend urgent feature")
        content_area.pack_start(self.tags_entry, False, False, 0)

        self.show_all()
        self.text_entry.grab_focus()

    def get_todo_data(self):
        """Get the TODO data.

        Returns:
            Tuple of (text, tags) or None
        """
        text = self.text_entry.get_text().strip()
        if not text:
            return None

        tags_text = self.tags_entry.get_text().strip()
        tags = [tag.strip() for tag in tags_text.split() if tag.strip()]

        return (text, tags)


class EditTodoDialog(Gtk.Dialog):
    """Dialog to edit an existing TODO."""

    def __init__(self, parent: Optional[Gtk.Window], todo: dict):
        """Initialize the edit TODO dialog.

        Args:
            parent: Parent window
            todo: TODO dictionary
        """
        super().__init__(
            title="Edit TODO",
            parent=parent,
            modal=True,
            destroy_with_parent=True
        )

        self.todo = todo

        self.set_default_size(500, 200)
        self.set_border_width(10)

        # Add buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        # Create content
        content_area = self.get_content_area()
        content_area.set_spacing(10)

        # TODO text
        label = Gtk.Label(label="TODO:", xalign=0)
        content_area.pack_start(label, False, False, 0)

        self.text_entry = Gtk.Entry()
        self.text_entry.set_text(todo['text'])
        self.text_entry.set_activates_default(True)
        content_area.pack_start(self.text_entry, False, False, 0)

        # Tags
        tags_label = Gtk.Label(label="Tags (space-separated):", xalign=0)
        content_area.pack_start(tags_label, False, False, 0)

        self.tags_entry = Gtk.Entry()
        tags_text = ' '.join(todo.get('tags', []))
        self.tags_entry.set_text(tags_text)
        content_area.pack_start(self.tags_entry, False, False, 0)

        self.show_all()
        self.text_entry.grab_focus()

    def get_todo_data(self):
        """Get the TODO data.

        Returns:
            Tuple of (text, tags) or None
        """
        text = self.text_entry.get_text().strip()
        if not text:
            return None

        tags_text = self.tags_entry.get_text().strip()
        tags = [tag.strip() for tag in tags_text.split() if tag.strip()]

        return (text, tags)
