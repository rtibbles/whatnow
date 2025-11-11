"""Ping dialog for activity tracking."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from datetime import datetime
from typing import Optional, Callable, Tuple


class PingDialog(Gtk.Dialog):
    """Dialog that appears when a ping is triggered."""

    def __init__(self, parent: Optional[Gtk.Window], timestamp: int,
                 callback: Optional[Callable[[int, str, list, str], None]] = None):
        """Initialize the ping dialog.

        Args:
            parent: Parent window
            timestamp: Unix timestamp of the ping
            callback: Function to call with (timestamp, activity, tags, notes) when submitted
        """
        super().__init__(
            title="WhatNow - Activity Ping",
            parent=parent,
            modal=True,
            destroy_with_parent=True
        )

        self.timestamp = timestamp
        self.callback = callback

        # Set dialog size
        self.set_default_size(500, 300)
        self.set_border_width(10)

        # Add buttons
        self.add_button("Skip", Gtk.ResponseType.CANCEL)
        self.add_button("Submit", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        # Create content
        content_area = self.get_content_area()
        content_area.set_spacing(10)

        # Timestamp label
        dt = datetime.fromtimestamp(timestamp)
        time_label = Gtk.Label()
        time_label.set_markup(
            f"<b>What are you doing right now?</b>\n"
            f"<small>{dt.strftime('%Y-%m-%d %H:%M:%S')}</small>"
        )
        time_label.set_line_wrap(True)
        content_area.pack_start(time_label, False, False, 5)

        # Activity entry
        activity_label = Gtk.Label(label="Activity:", xalign=0)
        content_area.pack_start(activity_label, False, False, 0)

        self.activity_entry = Gtk.Entry()
        self.activity_entry.set_placeholder_text("What are you doing?")
        self.activity_entry.set_activates_default(True)
        content_area.pack_start(self.activity_entry, False, False, 0)

        # Tags entry
        tags_label = Gtk.Label(label="Tags (space-separated):", xalign=0)
        content_area.pack_start(tags_label, False, False, 0)

        self.tags_entry = Gtk.Entry()
        self.tags_entry.set_placeholder_text("e.g., work coding meeting")
        content_area.pack_start(self.tags_entry, False, False, 0)

        # Notes text view
        notes_label = Gtk.Label(label="Additional notes (optional):", xalign=0)
        content_area.pack_start(notes_label, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(100)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.notes_textview = Gtk.TextView()
        self.notes_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.add(self.notes_textview)
        content_area.pack_start(scrolled, True, True, 0)

        # Show all widgets
        self.show_all()

        # Focus on activity entry
        self.activity_entry.grab_focus()

    def get_response_data(self) -> Optional[Tuple[int, str, list, str]]:
        """Get the data from the dialog.

        Returns:
            Tuple of (timestamp, activity, tags, notes) or None if cancelled
        """
        activity = self.activity_entry.get_text().strip()
        if not activity:
            return None

        # Parse tags
        tags_text = self.tags_entry.get_text().strip()
        tags = [tag.strip() for tag in tags_text.split() if tag.strip()]

        # Get notes
        notes_buffer = self.notes_textview.get_buffer()
        start_iter = notes_buffer.get_start_iter()
        end_iter = notes_buffer.get_end_iter()
        notes = notes_buffer.get_text(start_iter, end_iter, True).strip()

        return (self.timestamp, activity, tags, notes if notes else None)

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


def show_ping_dialog(parent: Optional[Gtk.Window], timestamp: int,
                     callback: Optional[Callable[[int, str, list, str], None]] = None) -> bool:
    """Show a ping dialog and return whether activity was logged.

    Args:
        parent: Parent window
        timestamp: Unix timestamp of the ping
        callback: Function to call with ping data

    Returns:
        True if activity was logged, False if cancelled
    """
    dialog = PingDialog(parent, timestamp, callback)
    return dialog.run_and_process()
