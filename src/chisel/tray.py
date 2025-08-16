"""
System tray interface for Chisel application.

Provides background operation, settings access, and status indication.
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal
from pathlib import Path
from loguru import logger

from .about_window import AboutWindow


class SystemTrayIcon(QSystemTrayIcon):
    """System tray icon with context menu for Chisel application."""

    # Signals
    settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # About window instance
        self.about_window = None

        # Set up tray icon
        self.setup_icon()

        # Create context menu
        self.setup_menu()

        # Connect signals
        self.activated.connect(self.on_tray_activated)

        logger.info("System tray icon initialized")

    def setup_icon(self) -> None:
        """Set up the tray icon."""
        # Try to load custom icon, fallback to default
        icon_path = Path("resources/icons/chisel_tray.png")

        if icon_path.exists():
            self.setIcon(QIcon(str(icon_path)))
        else:
            # Use default system icon
            app = QApplication.instance()
            if app:
                style = app.style()
                self.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
            else:
                # Fallback to empty icon
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