"""
Text processing workflow for Chisel application.

Handles text capture, AI processing, and text replacement operations.
"""

import asyncio
import time
from typing import Optional
from pynput import keyboard
from loguru import logger

from .ai_client import GeminiClient
from .settings import ChiselSettings
from .clipboard import ClipboardManager


class TextProcessor:
    """Manages the core text processing workflow."""
    
    def __init__(self, ai_client: Optional[GeminiClient], settings: ChiselSettings):
        self.ai_client = ai_client
        self.settings = settings
        self.keyboard = keyboard.Controller()
        self.clipboard = ClipboardManager()
        
        logger.info("Text processor initialized")
    
    async def process_selected_text(self) -> bool:
        """
        Main text processing workflow.
        
        Returns:
            bool: True if processing was successful
        """
        if not self.ai_client:
            logger.error("No AI client available")
            return False
        
        # Backup current clipboard
        original_clipboard = self.clipboard.get_clipboard_safely()
        logger.debug("Original clipboard backed up")
        
        try:
            # Step 1: Capture selected text
            selected_text = await self.capture_selected_text()
            if not selected_text:
                logger.warning("No text was captured")
                return False
            
            # Check text length
            if len(selected_text) > self.settings.max_text_length:
                logger.warning(f"Text too long: {len(selected_text)} > {self.settings.max_text_length}")
                return False
            
            logger.info(f"Captured text: {len(selected_text)} characters")
            
            # Step 2: Process with AI
            processed_text = await self.ai_client.process_text(
                text=selected_text,
                prompt=self.settings.current_prompt,
                temperature=self.settings.temperature,
                top_p=self.settings.top_p
            )
            
            if not processed_text:
                logger.error("AI processing returned empty result")
                return False
            
            logger.info(f"AI processed text: {len(processed_text)} characters")
            
            # Step 3: Replace original text
            success = self.replace_selected_text(processed_text)
            
            if success:
                logger.info("Text processing completed successfully")
                return True
            else:
                logger.error("Failed to replace text")
                return False
                
        except Exception as e:
            logger.error(f"Error during text processing: {e}")
            return False
            
        finally:
            # Restore original clipboard after a delay
            if original_clipboard:
                await asyncio.sleep(0.5)  # Give time for paste operation
                self.clipboard.set_clipboard_safely(original_clipboard)
                logger.debug("Original clipboard restored")
    
    async def capture_selected_text(self) -> Optional[str]:
        """
        Capture selected text using clipboard operations.
        
        Returns:
            Optional[str]: The captured text, or None if capture failed
        """
        max_retries = 3
        base_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                # Clear clipboard
                self.clipboard.clear()
                await asyncio.sleep(0.05)
                
                # Simulate Ctrl+C to copy selected text
                self.keyboard.press(keyboard.Key.ctrl)
                self.keyboard.press('c')
                self.keyboard.release('c')
                self.keyboard.release(keyboard.Key.ctrl)
                
                # Wait with increasing delay
                delay = base_delay * (attempt + 1)
                await asyncio.sleep(delay)
                
                # Check if clipboard has new content
                clipboard_content = self.clipboard.get_clipboard_safely()
                
                if clipboard_content and clipboard_content.strip():
                    logger.debug(f"Text captured on attempt {attempt + 1}")
                    return clipboard_content.strip()
                
                logger.debug(f"Capture attempt {attempt + 1} failed, retrying...")
                
            except Exception as e:
                logger.warning(f"Error during capture attempt {attempt + 1}: {e}")
        
        logger.error("Failed to capture selected text after all retries")
        return None
    
    def replace_selected_text(self, new_text: str) -> bool:
        """
        Replace selected text with processed text.
        
        Args:
            new_text: The text to paste
            
        Returns:
            bool: True if replacement was successful
        """
        try:
            # Copy new text to clipboard
            self.clipboard.set_clipboard_safely(new_text)
            
            # Small delay to ensure clipboard is updated
            time.sleep(0.1)
            
            # Simulate Ctrl+V to paste new text
            self.keyboard.press(keyboard.Key.ctrl)
            self.keyboard.press('v')
            self.keyboard.release('v')
            self.keyboard.release(keyboard.Key.ctrl)
            
            logger.debug("Text replacement completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during text replacement: {e}")
            return False
    
    def validate_text(self, text: str) -> bool:
        """
        Validate text before processing.
        
        Args:
            text: Text to validate
            
        Returns:
            bool: True if text is valid for processing
        """
        if not text or not text.strip():
            return False
        
        if len(text) > self.settings.max_text_length:
            return False
        
        # Check for potentially sensitive content (basic check)
        sensitive_patterns = [
            "password", "token", "key", "secret",
            "credit card", "ssn", "social security"
        ]
        
        text_lower = text.lower()
        for pattern in sensitive_patterns:
            if pattern in text_lower:
                logger.warning(f"Potentially sensitive content detected: {pattern}")
                return False
        
        return True