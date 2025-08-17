"""Stylesheet loader utility for efficient loading and management of QSS files."""

from pathlib import Path
from typing import Optional, Dict
from loguru import logger
from PyQt6.QtWidgets import QWidget


class StylesheetLoader:
    """Utility class for loading and managing QSS stylesheets.

    Features:
    - Caching for performance
    - Error handling with fallbacks
    - Hot reloading support for development
    - Component-specific stylesheet loading
    """

    _cache: Dict[str, str] = {}
    _base_path: Optional[Path] = None

    @classmethod
    def set_base_path(cls, path: Path) -> None:
        """Set the base path for stylesheet files.

        Args:
            path: Base directory containing stylesheet files
        """
        cls._base_path = path
        logger.info(f"Stylesheet base path set to: {path}")

    @classmethod
    def load_stylesheet(cls, filename: str, use_cache: bool = True) -> str:
        """Load a stylesheet from file.

        Args:
            filename: Name of the stylesheet file (e.g., 'main.qss')
            use_cache: Whether to use cached version if available

        Returns:
            Stylesheet content as string, empty string if loading fails
        """
        if use_cache and filename in cls._cache:
            logger.debug(f"Using cached stylesheet: {filename}")
            return cls._cache[filename]

        if cls._base_path is None:
            # Auto-detect base path relative to this file
            cls._base_path = Path(__file__).parent
            logger.info(f"Auto-detected stylesheet base path: {cls._base_path}")

        stylesheet_path = cls._base_path / filename

        try:
            if not stylesheet_path.exists():
                logger.error(f"Stylesheet file not found: {stylesheet_path}")
                return ""

            with open(stylesheet_path, 'r', encoding='utf-8') as file:
                content = file.read()

            cls._cache[filename] = content
            logger.info(f"Loaded stylesheet: {filename} ({len(content)} characters)")
            return content

        except Exception as e:
            logger.error(f"Failed to load stylesheet {filename}: {e}")
            return ""

    @classmethod
    def apply_stylesheet(cls, widget: QWidget, filename: str = "main.qss",
                        use_cache: bool = True) -> bool:
        """Apply a stylesheet to a widget.

        Args:
            widget: Widget to apply stylesheet to
            filename: Name of the stylesheet file
            use_cache: Whether to use cached version if available

        Returns:
            True if stylesheet was applied successfully, False otherwise
        """
        stylesheet = cls.load_stylesheet(filename, use_cache)

        if not stylesheet:
            logger.warning(f"No stylesheet content to apply for {filename}")
            return False

        try:
            widget.setStyleSheet(stylesheet)
            logger.debug(f"Applied stylesheet {filename} to {widget.__class__.__name__}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply stylesheet to widget: {e}")
            return False

    @classmethod
    def reload_stylesheet(cls, filename: str) -> str:
        """Force reload a stylesheet from disk, bypassing cache.

        Args:
            filename: Name of the stylesheet file

        Returns:
            Reloaded stylesheet content
        """
        if filename in cls._cache:
            del cls._cache[filename]
            logger.debug(f"Cleared cache for stylesheet: {filename}")

        return cls.load_stylesheet(filename, use_cache=False)

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached stylesheets."""
        cls._cache.clear()
        logger.info("Stylesheet cache cleared")

    @classmethod
    def get_cached_files(cls) -> list[str]:
        """Get list of currently cached stylesheet files.

        Returns:
            List of cached stylesheet filenames
        """
        return list(cls._cache.keys())

    @classmethod
    def preload_stylesheets(cls, filenames: list[str]) -> None:
        """Preload multiple stylesheets into cache.

        Args:
            filenames: List of stylesheet filenames to preload
        """
        logger.info(f"Preloading {len(filenames)} stylesheets...")

        for filename in filenames:
            cls.load_stylesheet(filename, use_cache=True)

        logger.info(f"Preloaded {len(cls._cache)} stylesheets")


# Convenience functions for common operations
def load_main_stylesheet() -> str:
    """Load the main application stylesheet.

    Returns:
        Main stylesheet content
    """
    return StylesheetLoader.load_stylesheet("main.qss")


def apply_main_stylesheet(widget: QWidget) -> bool:
    """Apply the main stylesheet to a widget and set application font.

    Args:
        widget: Widget to apply stylesheet to

    Returns:
        True if successful, False otherwise
    """
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import QApplication

    # Set application-wide font to ensure SF Pro is used
    app = QApplication.instance()
    if app:
        sfpro_font = QFont("SF Pro", 10)
        app.setFont(sfpro_font)
        logger.debug("Set application font to SF Pro")

    return StylesheetLoader.apply_stylesheet(widget, "main.qss")