"""
Settings dialog for Chisel application.

Provides a user interface for configuring API keys, AI parameters, and application settings.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox,
    QPushButton, QLabel, QTextEdit, QMessageBox, QTabWidget,
    QWidget, QSlider, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont
from typing import Optional, List
import asyncio
from loguru import logger

from .settings import ChiselSettings, SettingsManager
from .ai_client import GeminiClient, ModelInfo


class ModelFetchWorker(QThread):
    """Worker thread to fetch models from Google API."""
    
    models_fetched = pyqtSignal(list)  # List[ModelInfo]
    fetch_error = pyqtSignal(str)
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
    
    def run(self):
        """Fetch models in background thread."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            models = loop.run_until_complete(
                GeminiClient.fetch_models_static(self.api_key, timeout=10)
            )
            
            self.models_fetched.emit(models)
            
        except Exception as e:
            self.fetch_error.emit(str(e))
        finally:
            loop.close()


class SettingsDialog(QDialog):
    """Settings configuration dialog."""
    
    settings_changed = pyqtSignal(ChiselSettings)
    
    def __init__(self, current_settings: ChiselSettings, parent=None):
        super().__init__(parent)
        self.current_settings = current_settings
        self.settings_manager = SettingsManager()
        self.available_models: List[ModelInfo] = []
        self.model_fetch_worker: Optional[ModelFetchWorker] = None
        
        self.setWindowTitle("Chisel Settings")
        self.setModal(True)
        self.resize(500, 600)
        
        self.setup_ui()
        self.load_current_settings()
        
        # Start fetching models if API key is available
        if current_settings.api_key:
            self.fetch_models()
        
        logger.info("Settings dialog initialized")
    
    def setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Add tabs
        tabs.addTab(self.create_api_tab(), "AI Configuration")
        tabs.addTab(self.create_behavior_tab(), "Behavior")
        tabs.addTab(self.create_advanced_tab(), "Advanced")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Test Connection button
        self.test_button = QPushButton("Test API Connection")
        self.test_button.clicked.connect(self.test_api_connection)
        button_layout.addWidget(self.test_button)
        
        button_layout.addStretch()
        
        # Standard buttons
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        save_button.setDefault(True)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
    
    def create_api_tab(self) -> QWidget:
        """Create the API configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # API Configuration Group
        api_group = QGroupBox("Google AI Configuration")
        api_layout = QFormLayout(api_group)
        
        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Enter your Google AI API key")
        self.api_key_edit.textChanged.connect(self.on_api_key_changed)
        api_layout.addRow("API Key:", self.api_key_edit)
        
        # Show/Hide API Key
        self.show_key_checkbox = QCheckBox("Show API key")
        self.show_key_checkbox.toggled.connect(self.toggle_api_key_visibility)
        api_layout.addRow("", self.show_key_checkbox)
        
        # AI Model Selection
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(300)
        model_layout.addWidget(self.model_combo)
        
        # Refresh models button
        self.refresh_models_btn = QPushButton("🔄")
        self.refresh_models_btn.setMaximumWidth(30)
        self.refresh_models_btn.setToolTip("Refresh available models")
        self.refresh_models_btn.clicked.connect(self.refresh_models)
        model_layout.addWidget(self.refresh_models_btn)
        
        # Model loading indicator
        self.model_loading_label = QLabel("Loading models...")
        self.model_loading_label.setStyleSheet("color: gray; font-size: 9pt;")
        self.model_loading_label.hide()
        model_layout.addWidget(self.model_loading_label)
        
        api_layout.addRow("AI Model:", model_layout)
        
        # Initialize with fallback models (this will be overridden by load_current_settings)
        self.populate_fallback_models()
        
        layout.addWidget(api_group)
        
        # AI Parameters Group
        params_group = QGroupBox("AI Generation Parameters")
        params_layout = QFormLayout(params_group)
        
        # Temperature
        temp_layout = QHBoxLayout()
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(0, 100)
        self.temperature_slider.setValue(70)
        self.temperature_slider.valueChanged.connect(self.update_temperature_label)
        
        self.temperature_label = QLabel("0.70")
        self.temperature_label.setMinimumWidth(40)
        
        temp_layout.addWidget(self.temperature_slider)
        temp_layout.addWidget(self.temperature_label)
        
        params_layout.addRow("Temperature:", temp_layout)
        
        # Top-P
        top_p_layout = QHBoxLayout()
        self.top_p_slider = QSlider(Qt.Orientation.Horizontal)
        self.top_p_slider.setRange(0, 100)
        self.top_p_slider.setValue(80)
        self.top_p_slider.valueChanged.connect(self.update_top_p_label)
        
        self.top_p_label = QLabel("0.80")
        self.top_p_label.setMinimumWidth(40)
        
        top_p_layout.addWidget(self.top_p_slider)
        top_p_layout.addWidget(self.top_p_label)
        
        params_layout.addRow("Top-P:", top_p_layout)
        
        # Help text
        help_label = QLabel(
            "Temperature controls randomness (0.0 = deterministic, 1.0 = very creative).\\n"
            "Top-P controls diversity of word selection."
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: gray; font-size: 9pt;")
        params_layout.addRow("", help_label)
        
        layout.addWidget(params_group)
        
        # Custom Prompt Group
        prompt_group = QGroupBox("Default Prompt")
        prompt_layout = QVBoxLayout(prompt_group)
        
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setMaximumHeight(100)
        self.prompt_edit.setPlaceholderText("Enter the default prompt for AI processing...")
        prompt_layout.addWidget(self.prompt_edit)
        
        # Prompt presets
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Presets:"))
        
        professional_btn = QPushButton("Professional")
        professional_btn.clicked.connect(lambda: self.set_prompt_preset(
            "Rephrase this text to be more professional and clear:"
        ))
        preset_layout.addWidget(professional_btn)
        
        casual_btn = QPushButton("Casual")
        casual_btn.clicked.connect(lambda: self.set_prompt_preset(
            "Rephrase this text to be more casual and friendly:"
        ))
        preset_layout.addWidget(casual_btn)
        
        concise_btn = QPushButton("Concise")
        concise_btn.clicked.connect(lambda: self.set_prompt_preset(
            "Make this text more concise while keeping the meaning:"
        ))
        preset_layout.addWidget(concise_btn)
        
        preset_layout.addStretch()
        prompt_layout.addLayout(preset_layout)
        
        layout.addWidget(prompt_group)
        layout.addStretch()
        
        return widget
    
    def create_behavior_tab(self) -> QWidget:
        """Create the behavior configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Hotkey Group
        hotkey_group = QGroupBox("Global Hotkey")
        hotkey_layout = QFormLayout(hotkey_group)
        
        self.hotkey_edit = QLineEdit()
        self.hotkey_edit.setPlaceholderText("e.g., <ctrl>+<shift>+r")
        hotkey_layout.addRow("Hotkey:", self.hotkey_edit)
        
        hotkey_help = QLabel(
            "Use pynput format: <ctrl>, <alt>, <shift>, <cmd> (macOS)\\n"
            "Example: <ctrl>+<shift>+r"
        )
        hotkey_help.setStyleSheet("color: gray; font-size: 9pt;")
        hotkey_layout.addRow("", hotkey_help)
        
        layout.addWidget(hotkey_group)
        
        # Notifications Group
        notify_group = QGroupBox("Notifications")
        notify_layout = QFormLayout(notify_group)
        
        self.notifications_checkbox = QCheckBox("Show system notifications")
        notify_layout.addRow("", self.notifications_checkbox)
        
        layout.addWidget(notify_group)
        
        # Startup Group
        startup_group = QGroupBox("Startup")
        startup_layout = QFormLayout(startup_group)
        
        self.auto_start_checkbox = QCheckBox("Start with Windows")
        startup_layout.addRow("", self.auto_start_checkbox)
        
        layout.addWidget(startup_group)
        
        layout.addStretch()
        return widget
    
    def create_advanced_tab(self) -> QWidget:
        """Create the advanced configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Performance Group
        perf_group = QGroupBox("Performance")
        perf_layout = QFormLayout(perf_group)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 120)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" seconds")
        perf_layout.addRow("API Timeout:", self.timeout_spin)
        
        self.max_length_spin = QSpinBox()
        self.max_length_spin.setRange(100, 50000)
        self.max_length_spin.setValue(5000)
        self.max_length_spin.setSuffix(" characters")
        perf_layout.addRow("Max Text Length:", self.max_length_spin)
        
        layout.addWidget(perf_group)
        
        # Debug Group
        debug_group = QGroupBox("Debug")
        debug_layout = QVBoxLayout(debug_group)
        
        reset_btn = QPushButton("Reset All Settings")
        reset_btn.clicked.connect(self.reset_settings)
        debug_layout.addWidget(reset_btn)
        
        layout.addWidget(debug_group)
        
        layout.addStretch()
        return widget
    
    def toggle_api_key_visibility(self, show: bool) -> None:
        """Toggle API key visibility."""
        if show:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def update_temperature_label(self, value: int) -> None:
        """Update temperature label."""
        temp = value / 100.0
        self.temperature_label.setText(f"{temp:.2f}")
    
    def update_top_p_label(self, value: int) -> None:
        """Update top-p label."""
        top_p = value / 100.0
        self.top_p_label.setText(f"{top_p:.2f}")
    
    def set_prompt_preset(self, prompt: str) -> None:
        """Set a prompt preset."""
        self.prompt_edit.setPlainText(prompt)
    
    def load_current_settings(self) -> None:
        """Load current settings into the UI."""
        # API Configuration
        if self.current_settings.api_key:
            self.api_key_edit.setText(self.current_settings.api_key)
        
        self.set_selected_model(self.current_settings.ai_model)
        
        self.prompt_edit.setPlainText(self.current_settings.current_prompt)
        
        # AI Parameters
        self.temperature_slider.setValue(int(self.current_settings.temperature * 100))
        self.top_p_slider.setValue(int(self.current_settings.top_p * 100))
        
        # Behavior
        self.hotkey_edit.setText(self.current_settings.global_hotkey)
        self.notifications_checkbox.setChecked(self.current_settings.show_notifications)
        self.auto_start_checkbox.setChecked(self.current_settings.auto_start)
        
        # Advanced
        self.timeout_spin.setValue(self.current_settings.api_timeout)
        self.max_length_spin.setValue(self.current_settings.max_text_length)
    
    def get_settings_from_ui(self) -> ChiselSettings:
        """Get settings from UI controls."""
        return ChiselSettings(
            # API Configuration
            api_key=self.api_key_edit.text().strip() or None,
            ai_model=self.get_selected_model_name(),
            current_prompt=self.prompt_edit.toPlainText().strip(),
            
            # AI Parameters
            temperature=self.temperature_slider.value() / 100.0,
            top_p=self.top_p_slider.value() / 100.0,
            
            # Behavior
            global_hotkey=self.hotkey_edit.text().strip(),
            show_notifications=self.notifications_checkbox.isChecked(),
            auto_start=self.auto_start_checkbox.isChecked(),
            
            # Advanced
            api_timeout=self.timeout_spin.value(),
            max_text_length=self.max_length_spin.value()
        )
    
    def save_settings(self) -> None:
        """Save settings and close dialog."""
        try:
            new_settings = self.get_settings_from_ui()
            
            # Validate settings
            if not new_settings.api_key:
                QMessageBox.warning(
                    self, 
                    "Missing API Key", 
                    "Please enter your Google AI API key."
                )
                return
            
            if not new_settings.current_prompt.strip():
                QMessageBox.warning(
                    self, 
                    "Missing Prompt", 
                    "Please enter a default prompt."
                )
                return
            
            # Save settings
            if self.settings_manager.save_settings(new_settings):
                self.settings_changed.emit(new_settings)
                self.accept()
                logger.info("Settings saved successfully")
            else:
                QMessageBox.critical(
                    self, 
                    "Save Error", 
                    "Failed to save settings. Please try again."
                )
                
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(
                self, 
                "Error", 
                f"Error saving settings: {str(e)}"
            )
    
    def test_api_connection(self) -> None:
        """Test the API connection."""
        api_key = self.api_key_edit.text().strip()
        
        if not api_key:
            QMessageBox.warning(
                self, 
                "Missing API Key", 
                "Please enter your API key before testing."
            )
            return
        
        # TODO: Implement actual API test
        QMessageBox.information(
            self, 
            "Test Connection", 
            "API connection test not yet implemented.\\n"
            "This will test your API key in a future version."
        )
    
    def reset_settings(self) -> None:
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?\\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            default_settings = ChiselSettings()
            self.current_settings = default_settings
            self.load_current_settings()
            logger.info("Settings reset to defaults")
    
    def populate_fallback_models(self) -> None:
        """Populate combo box with fallback models."""
        fallback_models = GeminiClient._get_fallback_models_static()
        self.available_models = fallback_models
        self.update_model_combo()
    
    def update_model_combo(self) -> None:
        """Update the model combo box with available models."""
        # Get the current model name (not display text)
        current_selection = self.model_combo.currentData()
        if current_selection is None and self.model_combo.count() > 0:
            # Fallback to current text if no data stored
            current_selection = self.model_combo.currentText()
        
        self.model_combo.clear()
        
        for model in self.available_models:
            # Use display name if available, otherwise use model name
            display_text = f"{model.display_name or model.name}"
            if model.description:
                display_text += f" - {model.description[:50]}..."
            
            self.model_combo.addItem(display_text, model.name)
        
        # Restore previous selection if available
        if current_selection:
            for i in range(self.model_combo.count()):
                if self.model_combo.itemData(i) == current_selection:
                    self.model_combo.setCurrentIndex(i)
                    logger.debug(f"Restored model selection: {current_selection}")
                    return
            
            # If not found in new models, add it as a custom entry
            self.model_combo.addItem(current_selection, current_selection)
            self.model_combo.setCurrentIndex(self.model_combo.count() - 1)
            logger.debug(f"Added custom model selection: {current_selection}")
    
    def fetch_models(self) -> None:
        """Start fetching models from API."""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            logger.warning("No API key available for model fetching")
            return
        
        # Stop any existing worker
        if self.model_fetch_worker and self.model_fetch_worker.isRunning():
            self.model_fetch_worker.terminate()
            self.model_fetch_worker.wait()
        
        # Start new worker
        self.model_fetch_worker = ModelFetchWorker(api_key)
        self.model_fetch_worker.models_fetched.connect(self.on_models_fetched)
        self.model_fetch_worker.fetch_error.connect(self.on_model_fetch_error)
        
        # Show loading state
        self.model_loading_label.setText("Loading models...")
        self.model_loading_label.show()
        self.refresh_models_btn.setEnabled(False)
        
        self.model_fetch_worker.start()
        logger.info("Started fetching models from API")
    
    def refresh_models(self) -> None:
        """Refresh models manually."""
        self.fetch_models()
    
    def on_models_fetched(self, models: List[ModelInfo]) -> None:
        """Handle successful model fetching."""
        self.available_models = models
        self.update_model_combo()
        
        # Hide loading state
        self.model_loading_label.hide()
        self.refresh_models_btn.setEnabled(True)
        
        logger.info(f"Successfully loaded {len(models)} models from API")
        
        # Show success message briefly
        self.model_loading_label.setText("✓ Models updated")
        self.model_loading_label.setStyleSheet("color: green; font-size: 9pt;")
        self.model_loading_label.show()
        
        # Hide success message after 2 seconds
        QTimer.singleShot(2000, self.model_loading_label.hide)
    
    def on_model_fetch_error(self, error_message: str) -> None:
        """Handle model fetching error."""
        self.model_loading_label.setText("⚠ Failed to load models")
        self.model_loading_label.setStyleSheet("color: red; font-size: 9pt;")
        self.refresh_models_btn.setEnabled(True)
        
        logger.error(f"Failed to fetch models: {error_message}")
        
        # Hide error message after 3 seconds
        QTimer.singleShot(3000, lambda: (
            self.model_loading_label.hide(),
            self.model_loading_label.setStyleSheet("color: gray; font-size: 9pt;")
        ))
    
    def get_selected_model_name(self) -> str:
        """Get the selected model name (not display name)."""
        current_data = self.model_combo.currentData()
        if current_data:
            return current_data
        
        # Fallback to current text if no data
        return self.model_combo.currentText()
    
    def set_selected_model(self, model_name: str) -> None:
        """Set the selected model by name."""
        logger.debug(f"Attempting to set model selection to: {model_name}")
        
        for i in range(self.model_combo.count()):
            item_data = self.model_combo.itemData(i)
            logger.debug(f"  Checking item {i}: data='{item_data}', text='{self.model_combo.itemText(i)}'")
            if item_data == model_name:
                self.model_combo.setCurrentIndex(i)
                logger.debug(f"  Successfully set selection to index {i}")
                return
        
        # If not found, add it as a custom entry
        logger.debug(f"Model '{model_name}' not found in combo, adding as custom entry")
        self.model_combo.addItem(model_name, model_name)
        self.model_combo.setCurrentIndex(self.model_combo.count() - 1)
        logger.debug(f"Added custom model and set to index {self.model_combo.count() - 1}")
    
    def on_api_key_changed(self) -> None:
        """Handle API key changes."""
        # Enable/disable refresh button based on API key availability
        has_key = bool(self.api_key_edit.text().strip())
        self.refresh_models_btn.setEnabled(has_key)
        
        # Auto-refresh models if we have a valid-looking API key
        api_key = self.api_key_edit.text().strip()
        if len(api_key) > 20:  # Basic validation - API keys are typically longer
            # Delay fetching to avoid too many requests while typing
            if hasattr(self, '_api_key_timer'):
                self._api_key_timer.stop()
            
            self._api_key_timer = QTimer()
            self._api_key_timer.setSingleShot(True)
            self._api_key_timer.timeout.connect(self.fetch_models)
            self._api_key_timer.start(1000)  # Wait 1 second after typing stops