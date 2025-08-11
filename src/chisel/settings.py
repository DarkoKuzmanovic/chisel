"""
Settings management for Chisel application.

Handles configuration persistence, API key secure storage, and settings validation.
"""

import json
import keyring
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum
from loguru import logger


class APIProvider(str, Enum):
    """Supported API providers."""
    GOOGLE = "google"
    OPENROUTER = "openrouter"


class ChiselSettings(BaseModel):
    """Application settings with validation."""
    
    # API Provider Configuration
    api_provider: APIProvider = Field(
        default=APIProvider.GOOGLE,
        description="AI API provider to use"
    )
    
    # Google API Configuration
    google_api_key: Optional[str] = None
    google_model: str = Field(
        default="gemini-2.5-pro",
        description="Google AI model to use"
    )
    
    # OpenRouter API Configuration  
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = Field(
        default="openai/gpt-oss-20b:free",
        description="OpenRouter model to use"
    )
    
    # Legacy field for backward compatibility
    api_key: Optional[str] = Field(
        default=None,
        description="Legacy API key field (mapped to current provider)"
    )
    ai_model: Optional[str] = Field(
        default=None,
        description="Legacy model field (mapped to current provider)"
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
    
    # Helper properties for current provider
    @property
    def current_api_key(self) -> Optional[str]:
        """Get API key for current provider."""
        if self.api_provider == APIProvider.GOOGLE:
            return self.google_api_key or self.api_key  # Fallback to legacy
        elif self.api_provider == APIProvider.OPENROUTER:
            return self.openrouter_api_key
        return None
    
    @property 
    def current_model(self) -> str:
        """Get model for current provider."""
        if self.api_provider == APIProvider.GOOGLE:
            return self.google_model or self.ai_model or "gemini-2.5-pro"
        elif self.api_provider == APIProvider.OPENROUTER:
            return self.openrouter_model
        return "gemini-2.5-pro"
    
    def set_current_api_key(self, api_key: str) -> None:
        """Set API key for current provider."""
        if self.api_provider == APIProvider.GOOGLE:
            self.google_api_key = api_key
        elif self.api_provider == APIProvider.OPENROUTER:
            self.openrouter_api_key = api_key
    
    def set_current_model(self, model: str) -> None:
        """Set model for current provider."""
        if self.api_provider == APIProvider.GOOGLE:
            self.google_model = model
        elif self.api_provider == APIProvider.OPENROUTER:
            self.openrouter_model = model


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
        
        # Load API keys from secure storage
        try:
            # Load Google API key (check both new and legacy keys)
            google_key = keyring.get_password(self.app_name, "google_api_key")
            if google_key:
                settings.google_api_key = google_key
                logger.info("Google API key loaded from keyring")
            else:
                # Fallback to legacy api_key for backward compatibility
                legacy_key = keyring.get_password(self.app_name, "api_key")
                if legacy_key:
                    settings.google_api_key = legacy_key
                    settings.api_key = legacy_key  # Keep for compatibility
                    logger.info("Legacy API key loaded from keyring")
            
            # Load OpenRouter API key
            openrouter_key = keyring.get_password(self.app_name, "openrouter_api_key")
            if openrouter_key:
                settings.openrouter_api_key = openrouter_key
                logger.info("OpenRouter API key loaded from keyring")
                
        except Exception as e:
            logger.error(f"Error loading API keys from keyring: {e}")
        
        return settings
    
    def save_settings(self, settings: ChiselSettings) -> bool:
        """Save settings to file and keyring."""
        try:
            # Save API keys securely
            try:
                # Save Google API key
                if settings.google_api_key:
                    keyring.set_password(self.app_name, "google_api_key", settings.google_api_key)
                    logger.info("Google API key saved to keyring")
                
                # Save OpenRouter API key
                if settings.openrouter_api_key:
                    keyring.set_password(self.app_name, "openrouter_api_key", settings.openrouter_api_key)
                    logger.info("OpenRouter API key saved to keyring")
                    
                # Save legacy api_key for backward compatibility
                if settings.api_key:
                    keyring.set_password(self.app_name, "api_key", settings.api_key)
                    
            except Exception as e:
                logger.error(f"Error saving API keys to keyring: {e}")
                return False
            
            # Save other settings to file (exclude all API keys)
            settings_dict = settings.dict(exclude={"api_key", "google_api_key", "openrouter_api_key"})
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