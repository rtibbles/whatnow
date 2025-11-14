"""Ping dialog for activity tracking."""

import gi

gi.require_version("Gtk", "3.0")
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from gi.repository import GLib, Gtk


class NewTODODialog(Gtk.Dialog):
    """Quick dialog to create a new TODO."""

    def __init__(self, parent: Optional[Gtk.Window]):
        """Initialize the new TODO dialog.

        Args:
            parent: Parent window
        """
        super().__init__(title="New TODO", parent=parent, modal=True, destroy_with_parent=True)

        self.set_default_size(400, 150)
        self.set_border_width(10)

        # Add buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Create", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        # Create content
        content_area = self.get_content_area()
        content_area.set_spacing(10)

        # TODO text entry
        label = Gtk.Label(label="TODO:", xalign=0)
        content_area.pack_start(label, False, False, 0)

        self.text_entry = Gtk.Entry()
        self.text_entry.set_placeholder_text("What needs to be done?")
        self.text_entry.set_activates_default(True)
        content_area.pack_start(self.text_entry, False, False, 0)

        # Tags entry
        tags_label = Gtk.Label(label="Tags (space-separated, optional):", xalign=0)
        content_area.pack_start(tags_label, False, False, 0)

        self.tags_entry = Gtk.Entry()
        self.tags_entry.set_placeholder_text("e.g., backend urgent")
        content_area.pack_start(self.tags_entry, False, False, 0)

        self.show_all()
        self.text_entry.grab_focus()

    def get_todo_data(self) -> Optional[Tuple[str, List[str]]]:
        """Get the TODO data.

        Returns:
            Tuple of (text, tags) or None if cancelled
        """
        text = self.text_entry.get_text().strip()
        if not text:
            return None

        tags_text = self.tags_entry.get_text().strip()
        tags = [tag.strip() for tag in tags_text.split() if tag.strip()]

        return (text, tags)


class PingDialog(Gtk.Dialog):
    """Dialog that appears when a ping is triggered."""

    def __init__(
        self,
        parent: Optional[Gtk.Window],
        timestamp: int,
        github_tasks: List[Dict[str, Any]],
        local_todos: List[Dict[str, Any]],
        db,
        callback: Optional[Callable[[int, str, str, list, Optional[str]], None]] = None,
    ):
        """Initialize the ping dialog.

        Args:
            parent: Parent window
            timestamp: Unix timestamp of the ping
            github_tasks: List of current iteration GitHub tasks
            local_todos: List of active local TODOs
            db: Database instance
            callback: Function to call with (timestamp, todo_id, todo_type, tags, notes) when submitted
        """
        super().__init__(
            title="WhatNow - What are you working on?",
            parent=parent,
            modal=True,
            destroy_with_parent=True,
        )

        self.timestamp = timestamp
        self.github_tasks = github_tasks
        self.local_todos = local_todos
        self.db = db
        self.callback = callback
        self.selected_todo_id: Optional[str] = None
        self.selected_todo_type: Optional[str] = None
        self.tag_checkboxes: dict[str, Gtk.CheckButton] = {}
        self.all_tags: set[str] = set()

        # Set dialog size
        self.set_default_size(600, 500)
        self.set_border_width(10)

        # Add buttons
        self.add_button("Dismiss", Gtk.ResponseType.CANCEL)
        self.add_button("Submit", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        # Create content
        content_area = self.get_content_area()
        content_area.set_spacing(10)

        # Timestamp label
        dt = datetime.fromtimestamp(timestamp)
        time_label = Gtk.Label()
        time_label.set_markup(
            f"<b>What are you working on right now?</b>\n"
            f"<small>{dt.strftime('%Y-%m-%d %H:%M:%S')}</small>"
        )
        time_label.set_line_wrap(True)
        content_area.pack_start(time_label, False, False, 5)

        # Create scrolled window for TODOs
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)

        # TODO list container
        self.todo_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        scrolled.add(self.todo_box)

        # Radio button group
        self.radio_group = None

        # Add GitHub tasks
        if github_tasks:
            gh_label = Gtk.Label(xalign=0)
            gh_label.set_markup("<b>GitHub Tasks (Current Iteration):</b>")
            self.todo_box.pack_start(gh_label, False, False, 5)

            for task in github_tasks:
                radio = Gtk.RadioButton.new_with_label_from_widget(self.radio_group, task["title"])
                if self.radio_group is None:
                    self.radio_group = radio
                radio.connect("toggled", self._on_todo_selected, task["id"], "github")
                self.todo_box.pack_start(radio, False, False, 0)

        # Add local TODOs
        if local_todos:
            local_label = Gtk.Label(xalign=0)
            local_label.set_markup("<b>My TODOs:</b>")
            self.todo_box.pack_start(local_label, False, False, 5)

            for todo in local_todos:
                radio = Gtk.RadioButton.new_with_label_from_widget(self.radio_group, todo["text"])
                if self.radio_group is None:
                    self.radio_group = radio
                radio.connect("toggled", self._on_todo_selected, str(todo["id"]), "local")
                self.todo_box.pack_start(radio, False, False, 0)

        # New TODO button
        new_todo_button = Gtk.Button(label="+ Create New TODO")
        new_todo_button.connect("clicked", self._on_new_todo_clicked)
        self.todo_box.pack_start(new_todo_button, False, False, 10)

        content_area.pack_start(scrolled, True, True, 0)

        # Separator
        content_area.pack_start(Gtk.Separator(), False, False, 5)

        # Tags section
        tags_label = Gtk.Label(label="Tags:", xalign=0)
        content_area.pack_start(tags_label, False, False, 0)

        # Tags container (will be populated dynamically)
        self.tags_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        content_area.pack_start(self.tags_box, False, False, 0)

        # Additional tags entry
        self.additional_tags_entry = Gtk.Entry()
        self.additional_tags_entry.set_placeholder_text("Add more tags (space-separated)")
        content_area.pack_start(self.additional_tags_entry, False, False, 0)

        # Notes section
        notes_label = Gtk.Label(label="Notes (optional):", xalign=0)
        content_area.pack_start(notes_label, False, False, 0)

        notes_scrolled = Gtk.ScrolledWindow()
        notes_scrolled.set_min_content_height(60)
        notes_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.notes_textview = Gtk.TextView()
        self.notes_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        notes_scrolled.add(self.notes_textview)
        content_area.pack_start(notes_scrolled, False, False, 0)

        # Show all widgets
        self.show_all()

    def _on_todo_selected(self, radio_button, todo_id: str, todo_type: str):
        """Handle TODO selection.

        Args:
            radio_button: The radio button that was toggled
            todo_id: ID of the selected TODO
            todo_type: Type of TODO ('github' or 'local')
        """
        if radio_button.get_active():
            self.selected_todo_id = todo_id
            self.selected_todo_type = todo_type

            # Update tags based on selected TODO
            self._update_tags_for_todo(todo_id, todo_type)

    def _update_tags_for_todo(self, todo_id: str, todo_type: str):
        """Update the tags checkboxes based on selected TODO.

        Args:
            todo_id: ID of the selected TODO
            todo_type: Type of TODO
        """
        # Clear existing tag checkboxes
        for child in self.tags_box.get_children():
            self.tags_box.remove(child)
        self.tag_checkboxes.clear()

        # Get tags for this TODO
        todo_tags = []
        if todo_type == "github":
            task = next((t for t in self.github_tasks if t["id"] == todo_id), None)
            if task:
                todo_tags = task.get("labels", [])
        elif todo_type == "local":
            todo = next((t for t in self.local_todos if str(t["id"]) == todo_id), None)
            if todo:
                todo_tags = todo.get("tags", [])

        # Add checkboxes for each tag
        if todo_tags:
            for tag in todo_tags:
                checkbox = Gtk.CheckButton(label=tag)
                checkbox.set_active(True)  # Pre-select existing tags
                self.tag_checkboxes[tag] = checkbox
                self.tags_box.pack_start(checkbox, False, False, 0)

            self.tags_box.show_all()

    def _on_new_todo_clicked(self, button):
        """Handle new TODO button click."""
        dialog = NewTODODialog(self)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            data = dialog.get_todo_data()
            if data:
                text, tags = data
                # Create new TODO in database
                todo_id = self.db.add_local_todo(text, tags)

                # Add to local_todos list
                new_todo = {"id": todo_id, "text": text, "tags": tags, "is_active": True}
                self.local_todos.append(new_todo)

                # Add radio button for new TODO
                radio = Gtk.RadioButton.new_with_label_from_widget(self.radio_group, text)
                radio.connect("toggled", self._on_todo_selected, str(todo_id), "local")
                self.todo_box.pack_start(radio, False, False, 0)
                radio.show()

                # Select the new TODO
                radio.set_active(True)

        dialog.destroy()

    def get_response_data(self) -> Optional[Tuple[int, str, str, list, Optional[str]]]:
        """Get the data from the dialog.

        Returns:
            Tuple of (timestamp, todo_id, todo_type, tags, notes) or None if no TODO selected
        """
        if not self.selected_todo_id or not self.selected_todo_type:
            return None

        # Collect selected tags
        tags = []
        for tag, checkbox in self.tag_checkboxes.items():
            if checkbox.get_active():
                tags.append(tag)

        # Add additional tags
        additional_tags_text = self.additional_tags_entry.get_text().strip()
        if additional_tags_text:
            additional_tags = [tag.strip() for tag in additional_tags_text.split() if tag.strip()]
            tags.extend(additional_tags)

        # Get notes
        notes_buffer = self.notes_textview.get_buffer()
        start_iter = notes_buffer.get_start_iter()
        end_iter = notes_buffer.get_end_iter()
        notes = notes_buffer.get_text(start_iter, end_iter, True).strip()

        # Update TODO tags in database if local TODO
        if self.selected_todo_type == "local" and tags:
            self.db.update_local_todo(int(self.selected_todo_id), tags=tags)

        return (
            self.timestamp,
            self.selected_todo_id,
            self.selected_todo_type,
            tags,
            notes if notes else None,
        )

    def run_and_process(self) -> bool:
        """Run the dialog and process the response.

        Returns:
            True if activity was logged, False if cancelled
        """
        response = self.run()

        if response == Gtk.ResponseType.OK:
            data = self.get_response_data()
            if data and self.callback:
                self.callback(*data)
                self.destroy()
                return True

        self.destroy()
        return False


def show_ping_dialog(
    parent: Optional[Gtk.Window],
    timestamp: int,
    github_tasks: List[Dict[str, Any]],
    local_todos: List[Dict[str, Any]],
    db,
    callback: Optional[Callable[[int, str, str, list, Optional[str]], None]] = None,
) -> bool:
    """Show a ping dialog and return whether activity was logged.

    Args:
        parent: Parent window
        timestamp: Unix timestamp of the ping
        github_tasks: List of GitHub tasks from current iteration
        local_todos: List of active local TODOs
        db: Database instance
        callback: Function to call with ping data

    Returns:
        True if activity was logged, False if cancelled
    """
    dialog = PingDialog(parent, timestamp, github_tasks, local_todos, db, callback)
    return dialog.run_and_process()
