"""
System tray interface for Chisel application.

Provides background operation, settings access, and status indication with themed icons.
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from pathlib import Path
from loguru import logger

from .about_window import AboutWindow
from .theme_utils import get_tray_icon, ThemeDetector


class SystemTrayIcon(QSystemTrayIcon):
    """System tray icon with context menu for Chisel application."""

    # Signals
    settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # About window instance
        self.about_window = None

                # Set up theme monitoring timer
        self.theme_timer = QTimer()
        self.theme_timer.timeout.connect(self.check_theme_change)
        self.theme_timer.start(30000)  # Check every 30 seconds
        self.current_dark_theme = None

        # Set up tray icon
        self.setup_icon()

        # Create context menu
        self.setup_menu()

        # Connect signals
        self.activated.connect(self.on_tray_activated)

        logger.info("System tray icon initialized with theme detection")

    def setup_icon(self) -> None:
        """Set up the tray icon with theme-appropriate coloring."""
        try:
            # Use themed SVG icon
            icon = get_tray_icon()
            self.setIcon(icon)

            # Store current theme state
            self.current_dark_theme = ThemeDetector.is_dark_theme()

            logger.info(f"Tray icon set with {'dark' if self.current_dark_theme else 'light'} theme")

        except Exception as e:
            logger.error(f"Error setting themed tray icon: {e}")
            # Fallback to system icon
            app = QApplication.instance()
            if app:
                style = app.style()
                self.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
            else:
                self.setIcon(QIcon())

        self.setToolTip("Chisel - AI Text Rephrasing")

    def setup_menu(self) -> None:
        """Create the context menu."""
        self.menu = QMenu()

        # Settings action
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        self.menu.addAction(settings_action)

        self.menu.addSeparator()

        # Status action (disabled, just for display)
        self.status_action = QAction("Initializing...", self)
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)

        self.menu.addSeparator()

        # About action
        about_action = QAction("About Chisel", self)
        about_action.triggered.connect(self.show_about)
        self.menu.addAction(about_action)

        self.menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(quit_action)

        # Set context menu
        self.setContextMenu(self.menu)

    def on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            logger.info("Tray icon double-clicked, opening settings")
            self.settings_requested.emit()
        elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            logger.info("Tray icon middle-clicked, showing about")
            self.show_about()

    def update_status(self, status: str) -> None:
        """Update the status display."""
        self.status_action.setText(status)
        self.setToolTip(f"Chisel - {status}")
        logger.debug(f"Status updated to: {status}")

    def show_message(self, title: str, message: str) -> None:
        """Show system notification."""
        self.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Information,
            3000  # 3 seconds
        )
        logger.info(f"Notification shown: {title} - {message}")

    def show_about(self) -> None:
        """Show the About window."""
        # Create window if it doesn't exist or has been closed
        if self.about_window is None or not self.about_window.isVisible():
            self.about_window = AboutWindow()
            logger.info("Created new About window instance")

        # Show, raise, and activate
        self.about_window.show()
        self.about_window.raise_()
        self.about_window.activateWindow()
        logger.info("About window shown")

    def check_theme_change(self) -> None:
        """Check if Windows theme has changed and update icon if necessary."""
        try:
            current_dark_theme = ThemeDetector.is_dark_theme()

            if self.current_dark_theme != current_dark_theme:
                logger.info(f"Theme change detected: {current_dark_theme}")
                self.current_dark_theme = current_dark_theme

                # Update the tray icon
                icon = get_tray_icon()
                self.setIcon(icon)

                logger.info(f"Tray icon updated for {'dark' if current_dark_theme else 'light'} theme")

        except Exception as e:
            logger.error(f"Error checking theme change: {e}")

    def cleanup(self) -> None:
        """Clean up resources when tray is destroyed."""
        if self.theme_timer:
            self.theme_timer.stop()
        logger.info("System tray cleaned up")