"""
Theme detection and icon utilities for Chisel application.

Provides Windows theme detection and PNG-based themed icons.
"""

import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from pathlib import Path
from loguru import logger

if sys.platform == "win32":
    try:
        import winreg
    except ImportError:
        winreg = None
else:
    winreg = None


class ThemeDetector:
    """Detects Windows theme (dark/light mode) and provides themed icons."""

    @staticmethod
    def is_dark_theme() -> bool:
        """Detect if Windows is using dark theme."""
        if sys.platform != "win32" or winreg is None:
            logger.warning("Theme detection only supported on Windows")
            return False

        try:
            # Check Windows registry for theme setting
            registry_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )

            # AppsUseLightTheme: 0 = dark theme, 1 = light theme
            apps_use_light_theme, _ = winreg.QueryValueEx(registry_key, "AppsUseLightTheme")
            winreg.CloseKey(registry_key)

            is_dark = apps_use_light_theme == 0
            logger.info(f"Windows theme detected: {'dark' if is_dark else 'light'}")
            return is_dark

        except (FileNotFoundError, OSError, WindowsError) as e:
            logger.warning(f"Could not detect Windows theme: {e}")
            return False

    @staticmethod
    def get_themed_icon_path() -> Path:
        """Get the appropriate PNG icon path based on current theme."""
        is_dark = ThemeDetector.is_dark_theme()

        # Use dark PNG for light theme, light PNG for dark theme (icons should contrast with theme)
        if is_dark:
            icon_path = Path("resources/icons/chisel-dark.png")  # Light icon for dark theme
        else:
            icon_path = Path("resources/icons/chisel-light.png")   # Dark icon for light theme

        return icon_path


def get_app_icon(size: QSize = QSize(32, 32)) -> QIcon:
    """Get the application icon with appropriate theming."""
    icon_path = ThemeDetector.get_themed_icon_path()

    if icon_path.exists():
        icon = QIcon(str(icon_path))
        theme_type = "light" if icon_path.name.endswith("light.png") else "dark"
        logger.info(f"Created themed icon: {theme_type} icon from {icon_path.name}")
        return icon
    else:
        logger.warning(f"Icon file not found: {icon_path}, using fallback")
        # Fallback to default icon if PNG fails
        from PyQt6.QtWidgets import QApplication, QStyle
        app = QApplication.instance()
        if app:
            style = app.style()
            return style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        return QIcon()


def get_tray_icon() -> QIcon:
    """Get the system tray icon with appropriate size and theming."""
    # System tray icons are typically 16x16 or 32x32
    return get_app_icon(QSize(32, 32))
