"""
Clipboard operations for Chisel application.

Provides safe clipboard handling with backup and restore functionality.
"""

import time
from typing import Optional
import pyperclip
from loguru import logger


class ClipboardManager:
    """Manages clipboard operations with safety and backup features."""
    
    def __init__(self):
        self._last_backup: Optional[str] = None
        logger.info("Clipboard manager initialized")
    
    def get_clipboard_safely(self) -> Optional[str]:
        """
        Safely get clipboard content.
        
        Returns:
            Optional[str]: Clipboard content or None if error
        """
        try:
            content = pyperclip.paste()
            logger.debug(f"Clipboard read: {len(content) if content else 0} characters")
            return content
        except Exception as e:
            logger.error(f"Error reading clipboard: {e}")
            return None
    
    def set_clipboard_safely(self, text: str) -> bool:
        """
        Safely set clipboard content.
        
        Args:
            text: Text to set in clipboard
            
        Returns:
            bool: True if successful
        """
        try:
            pyperclip.copy(text)
            logger.debug(f"Clipboard set: {len(text)} characters")
            return True
        except Exception as e:
            logger.error(f"Error setting clipboard: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear clipboard content.
        
        Returns:
            bool: True if successful
        """
        try:
            pyperclip.copy("")
            logger.debug("Clipboard cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing clipboard: {e}")
            return False
    
    def backup_clipboard(self) -> bool:
        """
        Backup current clipboard content.
        
        Returns:
            bool: True if backup was successful
        """
        content = self.get_clipboard_safely()
        if content is not None:
            self._last_backup = content
            logger.debug("Clipboard backed up")
            return True
        else:
            logger.warning("Failed to backup clipboard")
            return False
    
    def restore_clipboard(self) -> bool:
        """
        Restore previously backed up clipboard content.
        
        Returns:
            bool: True if restore was successful
        """
        if self._last_backup is not None:
            success = self.set_clipboard_safely(self._last_backup)
            if success:
                logger.debug("Clipboard restored from backup")
            else:
                logger.error("Failed to restore clipboard from backup")
            return success
        else:
            logger.warning("No clipboard backup available to restore")
            return False
    
    def wait_for_clipboard_change(self, timeout: float = 2.0) -> Optional[str]:
        """
        Wait for clipboard content to change.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            Optional[str]: New clipboard content or None if timeout/error
        """
        initial_content = self.get_clipboard_safely()
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_content = self.get_clipboard_safely()
            
            if current_content != initial_content:
                logger.debug("Clipboard change detected")
                return current_content
            
            time.sleep(0.05)  # Small delay between checks
        
        logger.debug("Clipboard change timeout")
        return None
    
    def is_clipboard_empty(self) -> bool:
        """
        Check if clipboard is empty or contains only whitespace.
        
        Returns:
            bool: True if clipboard is empty
        """
        content = self.get_clipboard_safely()
        return not content or not content.strip()
    
    def get_clipboard_info(self) -> dict:
        """
        Get information about current clipboard state.
        
        Returns:
            dict: Clipboard information
        """
        content = self.get_clipboard_safely()
        
        return {
            "has_content": content is not None,
            "is_empty": not content or not content.strip() if content else True,
            "length": len(content) if content else 0,
            "has_backup": self._last_backup is not None,
            "backup_length": len(self._last_backup) if self._last_backup else 0
        }