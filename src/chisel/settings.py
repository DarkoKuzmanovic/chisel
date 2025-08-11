"""
Settings management for Chisel application.

Handles configuration persistence, API key secure storage, and settings validation.
"""

import json
import keyring
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger


class ChiselSettings(BaseModel):
    """Application settings with validation."""
    
    # API Configuration
    api_key: Optional[str] = None
    ai_model: str = Field(
        default="gemini-1.5-pro-latest",
        description="Google AI model to use"
    )
    current_prompt: str = Field(
        default="Rephrase this text to be more professional and clear:",
        description="Default prompt for AI processing"
    )
    
    # AI Parameters
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperature for AI generation (0.0-1.0)"
    )
    top_p: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Top-p for AI generation (0.0-1.0)"
    )
    
    # Hotkey Configuration
    global_hotkey: str = Field(
        default="<ctrl>+<shift>+r",
        description="Global hotkey combination"
    )
    
    # UI Preferences
    show_notifications: bool = True
    auto_start: bool = False
    
    # Advanced Settings
    api_timeout: int = Field(default=30, ge=5, le=120)
    max_text_length: int = Field(default=5000, ge=100, le=50000)
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class SettingsManager:
    """Manages application settings persistence and secure storage."""
    
    def __init__(self):
        self.app_name = "Chisel"
        self.config_dir = Path.home() / ".chisel"
        self.config_file = self.config_dir / "settings.json"
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
    def load_settings(self) -> ChiselSettings:
        """Load settings from file and keyring."""
        settings = ChiselSettings()
        
        # Load from config file
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                settings = ChiselSettings(**data)
                logger.info("Settings loaded from config file")
            except Exception as e:
                logger.error(f"Error loading settings from file: {e}")
        else:
            logger.info("Config file not found, using default settings")
        
        # Load API key from secure storage
        try:
            api_key = keyring.get_password(self.app_name, "api_key")
            if api_key:
                settings.api_key = api_key
                logger.info("API key loaded from keyring")
        except Exception as e:
            logger.error(f"Error loading API key from keyring: {e}")
        
        return settings
    
    def save_settings(self, settings: ChiselSettings) -> bool:
        """Save settings to file and keyring."""
        try:
            # Save API key securely
            if settings.api_key:
                try:
                    keyring.set_password(self.app_name, "api_key", settings.api_key)
                    logger.info("API key saved to keyring")
                except Exception as e:
                    logger.error(f"Error saving API key to keyring: {e}")
                    return False
            
            # Save other settings to file
            settings_dict = settings.dict(exclude={"api_key"})
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, indent=2, ensure_ascii=False)
            
            logger.info("Settings saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def delete_api_key(self) -> bool:
        """Delete API key from secure storage."""
        try:
            keyring.delete_password(self.app_name, "api_key")
            logger.info("API key deleted from keyring")
            return True
        except Exception as e:
            logger.error(f"Error deleting API key: {e}")
            return False
    
    def reset_settings(self) -> bool:
        """Reset settings to defaults."""
        try:
            # Delete config file
            if self.config_file.exists():
                self.config_file.unlink()
            
            # Delete API key
            self.delete_api_key()
            
            logger.info("Settings reset to defaults")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            return False