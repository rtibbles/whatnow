"""System tray icon for background operation."""

import gi

gi.require_version("Gtk", "3.0")
from typing import Callable, Optional

from gi.repository import GLib, Gtk


class TrayIcon:
    """System tray icon for WhatNow."""

    def __init__(
        self,
        on_show: Optional[Callable] = None,
        on_settings: Optional[Callable] = None,
        on_work_toggle: Optional[Callable[[bool], None]] = None,
        on_quit: Optional[Callable] = None,
    ):
        """Initialize the tray icon.

        Args:
            on_show: Callback when "Show" is clicked
            on_settings: Callback when "Settings" is clicked
            on_work_toggle: Callback when work toggle is clicked (receives is_working bool)
            on_quit: Callback when "Quit" is clicked
        """
        self.on_show = on_show
        self.on_settings = on_settings
        self.on_work_toggle = on_work_toggle
        self.on_quit = on_quit
        self.is_working = False
        self.work_toggle_item = None

        # Try to use AppIndicator3 first (better for modern desktops)
        self.indicator = None
        self.status_icon = None

        try:
            gi.require_version("AppIndicator3", "0.1")
            from gi.repository import AppIndicator3

            self.indicator = AppIndicator3.Indicator.new(
                "whatnow",
                "appointment-soon",  # Stock icon name
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
            )
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self.indicator.set_title("WhatNow")
            self.indicator.set_menu(self._create_menu())

        except (ValueError, ImportError):
            # Fallback to Gtk.StatusIcon (deprecated but still works)
            self.status_icon = Gtk.StatusIcon()
            self.status_icon.set_from_icon_name("appointment-soon")
            self.status_icon.set_tooltip_text("WhatNow - Activity Tracker")
            self.status_icon.connect("activate", self._on_activate)
            self.status_icon.connect("popup-menu", self._on_popup_menu)

    def _create_menu(self) -> Gtk.Menu:
        """Create the context menu.

        Returns:
            Gtk.Menu instance
        """
        menu = Gtk.Menu()

        # Work toggle item
        self.work_toggle_item = Gtk.CheckMenuItem(label="Working")
        self.work_toggle_item.set_active(self.is_working)
        self.work_toggle_item.connect("toggled", self._on_work_toggle)
        menu.append(self.work_toggle_item)

        # Separator
        menu.append(Gtk.SeparatorMenuItem())

        # Show window item
        show_item = Gtk.MenuItem(label="Show Window")
        show_item.connect("activate", self._on_show_clicked)
        menu.append(show_item)

        # Settings item
        settings_item = Gtk.MenuItem(label="Settings")
        settings_item.connect("activate", self._on_settings_clicked)
        menu.append(settings_item)

        # Separator
        menu.append(Gtk.SeparatorMenuItem())

        # About item
        about_item = Gtk.MenuItem(label="About")
        about_item.connect("activate", self._on_about_clicked)
        menu.append(about_item)

        # Separator
        menu.append(Gtk.SeparatorMenuItem())

        # Quit item
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self._on_quit_clicked)
        menu.append(quit_item)

        menu.show_all()
        return menu

    def _on_activate(self, status_icon):
        """Handle status icon activation (left click)."""
        if self.on_show:
            self.on_show()

    def _on_popup_menu(self, status_icon, button, activate_time):
        """Handle status icon popup menu (right click)."""
        menu = self._create_menu()
        menu.popup(None, None, Gtk.StatusIcon.position_menu, status_icon, button, activate_time)

    def _on_show_clicked(self, menu_item):
        """Handle show window menu item."""
        if self.on_show:
            self.on_show()

    def _on_settings_clicked(self, menu_item):
        """Handle settings menu item."""
        if self.on_settings:
            self.on_settings()

    def _on_about_clicked(self, menu_item):
        """Handle about menu item."""
        dialog = Gtk.AboutDialog()
        dialog.set_program_name("WhatNow")
        dialog.set_version("0.1.0")
        dialog.set_comments(
            "TagTime-style activity tracker with\n"
            "GitHub Projects and Google Calendar integration"
        )
        dialog.set_website("https://github.com/yourusername/whatnow")
        dialog.set_website_label("GitHub Repository")
        dialog.set_license_type(Gtk.License.MIT_X11)
        dialog.run()
        dialog.destroy()

    def _on_quit_clicked(self, menu_item):
        """Handle quit menu item."""
        if self.on_quit:
            self.on_quit()

    def _on_work_toggle(self, check_menu_item):
        """Handle work toggle."""
        self.is_working = check_menu_item.get_active()
        if self.on_work_toggle:
            self.on_work_toggle(self.is_working)

    def set_working_status(self, is_working: bool):
        """Update the working status.

        Args:
            is_working: Whether currently working
        """
        self.is_working = is_working
        # Update menu if it exists
        if self.work_toggle_item:
            self.work_toggle_item.set_active(is_working)

        # Update tooltip
        if is_working:
            self.set_tooltip("WhatNow - Working")
        else:
            self.set_tooltip("WhatNow - Not Working")

    def update_tooltip_with_time(self, hours: float):
        """Update tooltip with working time.

        Args:
            hours: Hours worked today
        """
        if self.is_working:
            self.set_tooltip(f"WhatNow - Working ({hours:.1f}h today)")
        else:
            self.set_tooltip(f"WhatNow - Not Working ({hours:.1f}h today)")

    def set_tooltip(self, text: str):
        """Set the tooltip text.

        Args:
            text: Tooltip text
        """
        if self.status_icon:
            self.status_icon.set_tooltip_text(text)

    def show(self):
        """Show the tray icon."""
        if self.indicator:
            from gi.repository import AppIndicator3

            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        elif self.status_icon:
            self.status_icon.set_visible(True)

    def hide(self):
        """Hide the tray icon."""
        if self.indicator:
            from gi.repository import AppIndicator3

            self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
        elif self.status_icon:
            self.status_icon.set_visible(False)
