"""
Utility functions for Chisel application.

Common helper functions used across different modules.
"""

import re
import os
import platform
import subprocess
from typing import Optional, List, Dict, Any
from pathlib import Path
from loguru import logger


def validate_hotkey_format(hotkey: str) -> bool:
    """
    Validate hotkey format for pynput compatibility.
    
    Args:
        hotkey: Hotkey string to validate
        
    Returns:
        bool: True if format is valid
    """
    # Basic validation for pynput format
    pattern = r'^<[^>]+>(\+<[^>]+>)*$|^[a-zA-Z0-9](\+[a-zA-Z0-9])*$'
    return bool(re.match(pattern, hotkey))


def sanitize_text_for_api(text: str) -> str:
    """
    Sanitize text before sending to API.
    
    Args:
        text: Text to sanitize
        
    Returns:
        str: Sanitized text
    """
    # Remove or replace potentially problematic characters
    sanitized = text.strip()
    
    # Remove excessive whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Remove control characters except common ones
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', sanitized)
    
    return sanitized


def get_system_info() -> Dict[str, Any]:
    """
    Get system information for debugging.
    
    Returns:
        Dict[str, Any]: System information
    """
    return {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "platform_release": platform.release(),
        "architecture": platform.architecture(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "machine": platform.machine(),
        "node": platform.node(),
    }


def is_admin() -> bool:
    """
    Check if the application is running with admin privileges.
    
    Returns:
        bool: True if running as admin
    """
    try:
        if platform.system() == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            # Unix-like systems
            return os.geteuid() == 0
    except Exception:
        return False


def get_app_data_dir() -> Path:
    """
    Get the appropriate application data directory for the current platform.
    
    Returns:
        Path: Application data directory
    """
    system = platform.system()
    
    if system == "Windows":
        # Use APPDATA directory
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Chisel"
        else:
            return Path.home() / "AppData" / "Roaming" / "Chisel"
            
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Chisel"
        
    else:  # Linux and others
        # Follow XDG Base Directory Specification
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "chisel"
        else:
            return Path.home() / ".config" / "chisel"


def ensure_directory_exists(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to create
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def truncate_text(text: str, max_length: int = 100, ellipsis: str = "...") -> str:
    """
    Truncate text to specified length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        ellipsis: Ellipsis string to append
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(ellipsis)] + ellipsis


def parse_version(version_string: str) -> tuple:
    """
    Parse version string into tuple for comparison.
    
    Args:
        version_string: Version string (e.g., "1.2.3")
        
    Returns:
        tuple: Version components as integers
    """
    try:
        return tuple(map(int, version_string.split('.')))
    except ValueError:
        logger.warning(f"Invalid version string: {version_string}")
        return (0, 0, 0)


def is_text_too_long(text: str, max_length: int) -> bool:
    """
    Check if text exceeds maximum length.
    
    Args:
        text: Text to check
        max_length: Maximum allowed length
        
    Returns:
        bool: True if text is too long
    """
    return len(text) > max_length


def clean_text_for_display(text: str, max_lines: int = 5) -> str:
    """
    Clean text for safe display in UI.
    
    Args:
        text: Text to clean
        max_lines: Maximum number of lines to keep
        
    Returns:
        str: Cleaned text
    """
    # Split into lines and limit
    lines = text.split('\\n')[:max_lines]
    
    # Join back and truncate if needed
    result = '\\n'.join(lines)
    
    # Remove any remaining control characters
    result = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', result)
    
    return result


def get_clipboard_formats() -> List[str]:
    """
    Get available clipboard formats (platform-specific).
    
    Returns:
        List[str]: Available clipboard formats
    """
    formats = ["text/plain"]
    
    try:
        if platform.system() == "Windows":
            # Windows clipboard formats
            formats.extend([
                "CF_TEXT",
                "CF_UNICODETEXT", 
                "CF_OEMTEXT"
            ])
        elif platform.system() == "Darwin":
            # macOS clipboard formats
            formats.extend([
                "public.utf8-plain-text",
                "public.plain-text"
            ])
        else:
            # Linux clipboard formats
            formats.extend([
                "text/plain;charset=utf-8",
                "UTF8_STRING",
                "STRING"
            ])
    except Exception as e:
        logger.debug(f"Error getting clipboard formats: {e}")
    
    return formats