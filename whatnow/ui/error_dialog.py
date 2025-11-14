"""User-friendly error dialog for displaying errors to users."""

import gi

gi.require_version("Gtk", "3.0")
import logging
from typing import Optional

from gi.repository import Gtk

logger = logging.getLogger(__name__)


class ErrorDialog(Gtk.MessageDialog):
    """User-friendly error dialog with helpful messages and recovery suggestions."""

    def __init__(self, parent: Optional[Gtk.Window], error: Exception, context: str = ""):
        """Initialize error dialog.

        Args:
            parent: Parent window
            error: The exception that occurred
            context: Context description for the error (e.g., "syncing GitHub")
        """
        super().__init__(
            parent=parent,
            modal=True,
            destroy_with_parent=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=self._get_error_title(error, context),
        )

        self.set_title("Error")
        self.format_secondary_text(self._get_error_message(error, context))

        # Add details expander for technical details
        expander = Gtk.Expander(label="Technical Details")
        details_label = Gtk.Label()
        details_label.set_text(str(error))
        details_label.set_line_wrap(True)
        details_label.set_selectable(True)
        details_label.set_xalign(0)
        expander.add(details_label)

        content_area = self.get_content_area()
        content_area.pack_start(expander, True, True, 10)

        self.show_all()

    def _get_error_title(self, error: Exception, context: str) -> str:
        """Get user-friendly error title.

        Args:
            error: The exception
            context: Context description

        Returns:
            User-friendly title string
        """
        error_type = type(error).__name__

        if "Network" in error_type or "Connection" in error_type or "Timeout" in error_type:
            return f"Network Error{' while ' + context if context else ''}"
        elif "Permission" in error_type or "Forbidden" in error_type:
            return f"Permission Error{' while ' + context if context else ''}"
        elif "NotFound" in error_type:
            return f"Not Found{' while ' + context if context else ''}"
        elif "Authentication" in error_type or "Auth" in error_type:
            return f"Authentication Error{' while ' + context if context else ''}"
        else:
            return f"Error{' while ' + context if context else ''}"

    def _get_error_message(self, error: Exception, context: str) -> str:
        """Get user-friendly error message with recovery suggestions.

        Args:
            error: The exception
            context: Context description

        Returns:
            User-friendly message string
        """
        error_type = type(error).__name__
        error_str = str(error)

        # Network errors
        if "Network" in error_type or "Connection" in error_type or "Timeout" in error_type:
            return (
                "Could not connect to the server.\n\n"
                "Possible solutions:\n"
                "• Check your internet connection\n"
                "• The service may be temporarily unavailable\n"
                "• Try again in a few moments"
            )

        # GitHub-specific errors
        if "github" in context.lower():
            if "401" in error_str or "Unauthorized" in error_str:
                return (
                    "GitHub authentication failed.\n\n"
                    "Your personal access token may be invalid or expired.\n\n"
                    "To fix this:\n"
                    "• Go to Settings → GitHub\n"
                    "• Enter a valid personal access token\n"
                    "• Ensure the token has 'repo' and 'project' scopes"
                )
            elif "403" in error_str or "Forbidden" in error_str:
                return (
                    "Access to GitHub resource denied.\n\n"
                    "Possible causes:\n"
                    "• Your token doesn't have the required permissions\n"
                    "• You don't have access to this organization/project\n"
                    "• Rate limit exceeded (wait a few minutes)"
                )
            elif "404" in error_str or "Not Found" in error_str:
                return (
                    "GitHub project not found.\n\n"
                    "Please check:\n"
                    "• Organization/username is correct\n"
                    "• Project number is correct\n"
                    "• You have access to the project"
                )

        # Google Calendar-specific errors
        if "calendar" in context.lower() or "gcal" in context.lower():
            if "credentials" in error_str.lower() or "auth" in error_str.lower():
                return (
                    "Google Calendar authentication failed.\n\n"
                    "To fix this:\n"
                    "• Go to Settings → Google Calendar\n"
                    "• Click 'Connect Google Calendar'\n"
                    "• Complete the authorization in your browser"
                )
            elif "quota" in error_str.lower() or "rate" in error_str.lower():
                return (
                    "Google Calendar API quota exceeded.\n\n"
                    "The sync will automatically retry later.\n"
                    "If this persists, reduce the sync frequency in Settings."
                )

        # Database errors
        if "database" in context.lower() or "sqlite" in error_type.lower():
            return (
                "Database error occurred.\n\n"
                "This may indicate:\n"
                "• Database file is corrupted\n"
                "• Disk is full\n"
                "• File permissions issue\n\n"
                "Consider backing up your data and contacting support."
            )

        # Generic error
        return (
            f"An error occurred: {error_str}\n\n"
            "If this problem persists, please report it with the technical details below."
        )


def show_error_dialog(parent: Optional[Gtk.Window], error: Exception, context: str = ""):
    """Show an error dialog to the user.

    Args:
        parent: Parent window
        error: The exception that occurred
        context: Context description (e.g., "syncing GitHub")
    """
    logger.error(f"Error {context}: {error}", exc_info=True)

    dialog = ErrorDialog(parent, error, context)
    dialog.run()
    dialog.destroy()


def show_simple_error(parent: Optional[Gtk.Window], title: str, message: str):
    """Show a simple error dialog with custom title and message.

    Args:
        parent: Parent window
        title: Error title
        message: Error message
    """
    dialog = Gtk.MessageDialog(
        parent=parent,
        modal=True,
        destroy_with_parent=True,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text=title,
    )
    dialog.format_secondary_text(message)
    dialog.run()
    dialog.destroy()


def show_warning_dialog(parent: Optional[Gtk.Window], title: str, message: str) -> bool:
    """Show a warning dialog with OK/Cancel buttons.

    Args:
        parent: Parent window
        title: Warning title
        message: Warning message

    Returns:
        True if user clicked OK, False if cancelled
    """
    dialog = Gtk.MessageDialog(
        parent=parent,
        modal=True,
        destroy_with_parent=True,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.OK_CANCEL,
        text=title,
    )
    dialog.format_secondary_text(message)

    response: int = dialog.run()
    dialog.destroy()

    return bool(response == Gtk.ResponseType.OK)


def show_info_dialog(parent: Optional[Gtk.Window], title: str, message: str):
    """Show an informational dialog.

    Args:
        parent: Parent window
        title: Info title
        message: Info message
    """
    dialog = Gtk.MessageDialog(
        parent=parent,
        modal=True,
        destroy_with_parent=True,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text=title,
    )
    dialog.format_secondary_text(message)
    dialog.run()
    dialog.destroy()
