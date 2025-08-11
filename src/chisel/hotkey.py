"""
Global hotkey manager for Chisel application.

Provides cross-platform global hotkey registration and handling.
"""

import platform
from typing import Callable, List, Optional
from pynput import keyboard
from loguru import logger


class GlobalHotkeyManager:
    """Cross-platform global hotkey registration and management."""
    
    def __init__(self):
        self.listeners: List[keyboard.GlobalHotKeys] = []
        self.hotkey_callbacks: dict[str, Callable] = {}
        self.platform = platform.system().lower()
        
        logger.info(f"Global hotkey manager initialized for platform: {self.platform}")
    
    def register_hotkey(self, keys: str, callback: Callable) -> bool:
        """
        Register a global hotkey.
        
        Args:
            keys: Hotkey combination string (e.g., "<ctrl>+<shift>+r")
            callback: Function to call when hotkey is pressed
            
        Returns:
            bool: True if hotkey was registered successfully
        """
        try:
            # Store callback
            self.hotkey_callbacks[keys] = callback
            
            # Create hotkey listener
            hotkey_listener = keyboard.GlobalHotKeys({
                keys: callback
            })
            
            # Start listening
            hotkey_listener.start()
            self.listeners.append(hotkey_listener)
            
            logger.info(f"Global hotkey registered: {keys}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register global hotkey '{keys}': {e}")
            return False
    
    def unregister_hotkey(self, keys: str) -> bool:
        """
        Unregister a specific hotkey.
        
        Args:
            keys: Hotkey combination string to unregister
            
        Returns:
            bool: True if hotkey was unregistered successfully
        """
        try:
            # Find and stop the listener for this hotkey
            for i, listener in enumerate(self.listeners):
                if keys in self.hotkey_callbacks:
                    listener.stop()
                    self.listeners.pop(i)
                    del self.hotkey_callbacks[keys]
                    logger.info(f"Global hotkey unregistered: {keys}")
                    return True
            
            logger.warning(f"Hotkey not found for unregistration: {keys}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to unregister global hotkey '{keys}': {e}")
            return False
    
    def unregister_all(self) -> None:
        """Unregister all hotkeys and clean up listeners."""
        logger.info("Unregistering all global hotkeys")
        
        for listener in self.listeners:
            try:
                listener.stop()
            except Exception as e:
                logger.error(f"Error stopping hotkey listener: {e}")
        
        self.listeners.clear()
        self.hotkey_callbacks.clear()
        
        logger.info("All global hotkeys unregistered")
    
    def is_hotkey_available(self, keys: str) -> bool:
        """
        Check if a hotkey combination is available (not already registered).
        
        Args:
            keys: Hotkey combination string to check
            
        Returns:
            bool: True if hotkey is available
        """
        return keys not in self.hotkey_callbacks
    
    def get_platform_info(self) -> dict[str, str]:
        """
        Get platform-specific information for debugging.
        
        Returns:
            dict: Platform information
        """
        info = {
            "platform": self.platform,
            "system": platform.system(),
            "version": platform.version(),
            "architecture": platform.architecture()[0]
        }
        
        # Add platform-specific notes
        if self.platform == "windows":
            info["notes"] = "May require admin privileges for some applications"
        elif self.platform == "darwin":
            info["notes"] = "Requires accessibility permissions"
        elif self.platform == "linux":
            info["notes"] = "X11/Wayland compatibility may vary"
        else:
            info["notes"] = "Platform support may be limited"
        
        return info
    
    def test_hotkey(self, keys: str) -> bool:
        """
        Test if a hotkey can be registered (for validation).
        
        Args:
            keys: Hotkey combination string to test
            
        Returns:
            bool: True if hotkey can be registered
        """
        def test_callback():
            pass
        
        try:
            # Try to register temporarily
            test_listener = keyboard.GlobalHotKeys({keys: test_callback})
            test_listener.start()
            test_listener.stop()
            
            logger.debug(f"Hotkey test successful: {keys}")
            return True
            
        except Exception as e:
            logger.warning(f"Hotkey test failed for '{keys}': {e}")
            return False