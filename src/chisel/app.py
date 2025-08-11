"""
Main application controller for Chisel.

This module contains the main application class that coordinates all components
and handles the application lifecycle.
"""

import sys
import asyncio
from typing import Optional
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon
from PyQt6.QtCore import QTimer
from loguru import logger

from .settings import SettingsManager, ChiselSettings
from .settings_dialog import SettingsDialog
from .tray import SystemTrayIcon
from .hotkey import GlobalHotkeyManager
from .processor import TextProcessor
from .ai_client import AIClient, create_ai_client


class ChiselApp(QApplication):
    """Main application controller for Chisel."""
    
    def __init__(self, argv: list[str]):
        super().__init__(argv)
        
        # Initialize logging
        logger.add("chisel.log", rotation="1 MB", retention="10 days")
        logger.info("Starting Chisel application")
        
        # Core components
        self.settings_manager = SettingsManager()
        self.settings: Optional[ChiselSettings] = None
        self.tray_icon: Optional[SystemTrayIcon] = None
        self.hotkey_manager: Optional[GlobalHotkeyManager] = None
        self.text_processor: Optional[TextProcessor] = None
        self.ai_client: Optional[AIClient] = None
        
        # Application state
        self.is_ready = False
        
        # Set application properties
        self.setApplicationName("Chisel")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("Chisel")
        self.setOrganizationDomain("chisel.ai")
        
        # Prevent application from quitting when windows are closed
        self.setQuitOnLastWindowClosed(False)
        
    def initialize(self) -> bool:
        """Initialize all application components."""
        try:
            # Load settings
            self.settings = self.settings_manager.load_settings()
            
            # Initialize AI client
            if self.settings.current_api_key:
                self.ai_client = create_ai_client(
                    api_provider=self.settings.api_provider.value,
                    api_key=self.settings.current_api_key,
                    model=self.settings.current_model,
                    timeout=self.settings.api_timeout
                )
                if self.ai_client:
                    logger.info(f"AI client initialized: {self.settings.api_provider.value} with {self.settings.current_model}")
                else:
                    logger.error(f"Failed to create AI client for provider: {self.settings.api_provider.value}")
            else:
                logger.warning("No API key configured")
            
            # Initialize text processor
            self.text_processor = TextProcessor(self.ai_client, self.settings)
            
            # Initialize system tray
            self.tray_icon = SystemTrayIcon()
            self.tray_icon.settings_requested.connect(self.show_settings)
            self.tray_icon.quit_requested.connect(self.quit_application)
            self.tray_icon.show()
            
            # Initialize hotkey manager
            self.hotkey_manager = GlobalHotkeyManager()
            if not self.hotkey_manager.register_hotkey(
                self.settings.global_hotkey,
                self.on_hotkey_pressed
            ):
                logger.error("Failed to register global hotkey")
                self.tray_icon.show_message(
                    "Chisel Error", 
                    "Failed to register global hotkey. Please check settings."
                )
                return False
            
            # Update status
            self.is_ready = True
            self.tray_icon.update_status("Ready")
            logger.info("Chisel application initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            if self.tray_icon:
                self.tray_icon.show_message("Chisel Error", f"Initialization failed: {e}")
            return False
    
    def on_hotkey_pressed(self) -> None:
        """Handle global hotkey press."""
        if not self.is_ready or not self.text_processor:
            return
            
        logger.info("Global hotkey pressed")
        self.tray_icon.update_status("Processing...")
        
        # Schedule async processing
        QTimer.singleShot(0, self.process_text_async)
    
    def process_text_async(self) -> None:
        """Process text asynchronously."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            success = loop.run_until_complete(self.text_processor.process_selected_text())
            
            if success:
                logger.info("Text processed successfully")
            else:
                logger.warning("Text processing failed")
                
        except Exception as e:
            logger.error(f"Error during text processing: {e}")
        finally:
            loop.close()
            self.tray_icon.update_status("Ready")
    
    def show_settings(self) -> None:
        """Show settings dialog."""
        logger.info("Opening settings dialog")
        
        if not self.settings:
            logger.error("Settings not available")
            return
            
        try:
            dialog = SettingsDialog(self.settings)
            dialog.settings_changed.connect(self.on_settings_changed)
            
            if dialog.exec() == SettingsDialog.DialogCode.Accepted:
                logger.info("Settings dialog accepted")
            else:
                logger.info("Settings dialog cancelled")
                
        except Exception as e:
            logger.error(f"Error opening settings dialog: {e}")
            if self.tray_icon:
                self.tray_icon.show_message(
                    "Chisel Error", 
                    f"Failed to open settings: {e}"
                )
    
    def on_settings_changed(self, new_settings: ChiselSettings) -> None:
        """Handle settings changes."""
        logger.info("Settings updated, reinitializing components")
        
        # Update current settings
        self.settings = new_settings
        
        # Reinitialize AI client if API key or provider changed
        if new_settings.current_api_key:
            self.ai_client = create_ai_client(
                api_provider=new_settings.api_provider.value,
                api_key=new_settings.current_api_key,
                model=new_settings.current_model,
                timeout=new_settings.api_timeout
            )
            if self.ai_client:
                logger.info(f"AI client updated: {new_settings.api_provider.value} with {new_settings.current_model}")
            else:
                logger.error(f"Failed to create AI client for provider: {new_settings.api_provider.value}")
                if self.tray_icon:
                    self.tray_icon.show_message(
                        "Chisel Error", 
                        f"Failed to initialize {new_settings.api_provider.value} client"
                    )
            
            # Update text processor
            if self.text_processor:
                self.text_processor.ai_client = self.ai_client
                self.text_processor.settings = new_settings
        
        # Update hotkey if changed
        if self.hotkey_manager:
            self.hotkey_manager.unregister_all()
            if not self.hotkey_manager.register_hotkey(
                new_settings.global_hotkey,
                self.on_hotkey_pressed
            ):
                logger.error("Failed to register new hotkey")
                if self.tray_icon:
                    self.tray_icon.show_message(
                        "Chisel Warning", 
                        "Failed to register new hotkey"
                    )
        
        # Show success message
        if self.tray_icon:
            self.tray_icon.show_message("Chisel", "Settings updated successfully")
    
    def quit_application(self) -> None:
        """Clean shutdown of the application."""
        logger.info("Shutting down Chisel application")
        
        # Cleanup components
        if self.hotkey_manager:
            self.hotkey_manager.unregister_all()
        
        if self.tray_icon:
            self.tray_icon.hide()
        
        # Quit application
        self.quit()


def main() -> int:
    """Main entry point for the application."""
    # Create and initialize application
    app = ChiselApp(sys.argv)
    
    # Check for system tray support
    if not QSystemTrayIcon.isSystemTrayAvailable():
        logger.error("System tray is not available")
        return 1
    
    # Initialize application components
    if not app.initialize():
        logger.error("Failed to initialize application")
        return 1
    
    # Run application event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())