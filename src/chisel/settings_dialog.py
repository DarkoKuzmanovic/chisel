"""
Modern settings dialog for Chisel application.

Provides a modern, user-friendly interface for configuring API keys, AI parameters,
and application settings with comprehensive provider support.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox,
    QPushButton, QLabel, QTextEdit, QMessageBox, QTabWidget,
    QWidget, QSlider, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QPixmap
from typing import Optional, List
import asyncio
from loguru import logger

from .settings import ChiselSettings, SettingsManager, APIProvider
from .ai_client import GeminiClient, OpenRouterClient, ModelInfo, create_ai_client


class ModelFetchWorker(QThread):
    """Worker thread to fetch models from any API provider."""

    models_fetched = pyqtSignal(list)  # List[ModelInfo]
    fetch_error = pyqtSignal(str)

    def __init__(self, api_provider: APIProvider, api_key: str):
        super().__init__()
        self.api_provider = api_provider
        self.api_key = api_key

    def run(self):
        """Fetch models in background thread."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            if self.api_provider == APIProvider.GOOGLE:
                models = loop.run_until_complete(
                    GeminiClient.fetch_models_static(self.api_key, timeout=10)
                )
            elif self.api_provider == APIProvider.OPENROUTER:
                # Create temporary client to fetch models
                client = OpenRouterClient(self.api_key, timeout=10)
                models = loop.run_until_complete(client.fetch_available_models())
            else:
                raise ValueError(f"Unsupported provider: {self.api_provider}")

            self.models_fetched.emit(models)

        except Exception as e:
            self.fetch_error.emit(str(e))
        finally:
            loop.close()


class SettingsDialog(QDialog):
    """Modern settings configuration dialog."""

    settings_changed = pyqtSignal(ChiselSettings)

    def __init__(self, current_settings: ChiselSettings, parent=None):
        super().__init__(parent)
        self.current_settings = current_settings
        self.settings_manager = SettingsManager()
        self.available_models: List[ModelInfo] = []
        self.model_fetch_worker: Optional[ModelFetchWorker] = None

        self.setWindowTitle("Chisel Settings")
        self.setModal(True)
        self.resize(580, 700)

        # Apply global scrollbar styling to the entire dialog
        self.setStyleSheet("""
            /* Global scrollbar styling for the entire dialog */
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #ced4da;
                border-radius: 6px;
                margin: 2px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #adb5bd;
            }
            QScrollBar::handle:vertical:pressed {
                background-color: #6c757d;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #f8f9fa;
                height: 12px;
                border-radius: 6px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background-color: #ced4da;
                border-radius: 6px;
                margin: 2px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #adb5bd;
            }
            QScrollBar::handle:horizontal:pressed {
                background-color: #6c757d;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                width: 0px;
            }
            /* Ensure form labels are visible */
            QFormLayout QLabel {
                color: #495057;
                font-size: 14px;
                font-weight: 500;
            }
        """)

        self.setup_ui()
        self.load_current_settings()

        # Start fetching models if API key is available
        if current_settings.current_api_key:
            self.fetch_models()

        logger.info("Settings dialog initialized")

    def setup_ui(self) -> None:
        """Set up the modern user interface."""
        # Main layout with no margins for full-width sections
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header section
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border: none;
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(32, 24, 32, 24)
        header_layout.setSpacing(8)

        # Title and description
        title_label = QLabel("Settings")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: 700;
                background: transparent;
            }
        """)

        subtitle_label = QLabel("Configure your Chisel experience")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                font-weight: 400;
                background: transparent;
            }
        """)

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)

        # Content area
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: none;
            }
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(32, 24, 32, 0)

        # Tab widget with modern styling
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: white;
                border-radius: 12px;
                margin-top: 8px;
            }
            QTabBar::tab {
                background: transparent;
                color: #6c757d;
                border: none;
                padding: 12px 24px;
                margin-right: 4px;
                font-size: 14px;
                font-weight: 500;
                border-radius: 8px 8px 0px 0px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #495057;
                border-bottom: 3px solid #667eea;
            }
            QTabBar::tab:hover:!selected {
                background: rgba(255, 255, 255, 0.5);
                color: #495057;
            }
        """)

        # Create tabs
        self.create_api_tab()
        self.create_behavior_tab()
        self.create_advanced_tab()

        content_layout.addWidget(self.tab_widget)

        # Footer with action buttons
        footer = QFrame()
        footer.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid #dee2e6;
            }
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(32, 20, 32, 20)
        footer_layout.setSpacing(12)

        # Test Connection button
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_api_connection)
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)

        footer_layout.addWidget(self.test_button)
        footer_layout.addStretch()

        # Cancel and Save buttons
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)

        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setDefault(True)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #5a6fd8;
            }
            QPushButton:pressed {
                background-color: #4c63d2;
            }
        """)

        footer_layout.addWidget(self.cancel_button)
        footer_layout.addWidget(self.save_button)

        # Add all sections
        main_layout.addWidget(header)
        main_layout.addWidget(content_frame)
        main_layout.addWidget(footer)

    def create_api_tab(self) -> None:
        """Create the API configuration tab."""
        tab = QWidget()
        tab.setStyleSheet("""
            QWidget {
                background: white;
            }
        """)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        # Provider Selection Group
        provider_group = self.create_styled_group("API Provider")
        provider_layout = QFormLayout(provider_group)
        provider_layout.setSpacing(16)

        # Provider selection
        self.provider_combo = QComboBox()
        self.provider_combo.addItem("Google Gemini", APIProvider.GOOGLE.value)
        self.provider_combo.addItem("OpenRouter", APIProvider.OPENROUTER.value)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        self.style_input_widget(self.provider_combo)
        self.add_form_row(provider_layout, "Provider:", self.provider_combo)

        layout.addWidget(provider_group)

        # API Configuration Group
        self.api_group = self.create_styled_group("API Configuration")
        self.api_layout = QFormLayout(self.api_group)
        self.api_layout.setSpacing(16)

        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Enter your API key")
        self.api_key_edit.textChanged.connect(self.on_api_key_changed)
        self.style_input_widget(self.api_key_edit)
        self.add_form_row(self.api_layout, "API Key:", self.api_key_edit)

        # Show/Hide API Key
        self.show_key_checkbox = QCheckBox("Show API key")
        self.show_key_checkbox.toggled.connect(self.toggle_api_key_visibility)
        self.style_checkbox(self.show_key_checkbox)
        self.add_form_row(self.api_layout, "", self.show_key_checkbox)

        # AI Model Selection
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(300)
        self.style_input_widget(self.model_combo)
        model_layout.addWidget(self.model_combo)

        # Refresh models button
        self.refresh_models_btn = QPushButton("🔄")
        self.refresh_models_btn.setMaximumWidth(36)
        self.refresh_models_btn.setToolTip("Refresh available models")
        self.refresh_models_btn.clicked.connect(self.refresh_models)
        self.refresh_models_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)
        model_layout.addWidget(self.refresh_models_btn)

        # Model loading indicator
        self.model_loading_label = QLabel("Loading models...")
        self.model_loading_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        self.model_loading_label.hide()
        model_layout.addWidget(self.model_loading_label)

        self.add_form_row(self.api_layout, "AI Model:", model_layout)

        layout.addWidget(self.api_group)

        # Initialize with fallback models
        self.populate_fallback_models()

        # AI Parameters Group
        params_group = self.create_styled_group("AI Generation Parameters")
        params_layout = QFormLayout(params_group)
        params_layout.setSpacing(16)

        # Temperature
        temp_layout = QHBoxLayout()
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(0, 100)
        self.temperature_slider.setValue(70)
        self.temperature_slider.valueChanged.connect(self.update_temperature_label)
        self.style_slider(self.temperature_slider)

        self.temperature_label = QLabel("0.70")
        self.temperature_label.setMinimumWidth(40)
        self.temperature_label.setStyleSheet("color: #495057; font-weight: 500;")

        temp_layout.addWidget(self.temperature_slider)
        temp_layout.addWidget(self.temperature_label)

        self.add_form_row(params_layout, "Temperature:", temp_layout)

        # Top-P
        top_p_layout = QHBoxLayout()
        self.top_p_slider = QSlider(Qt.Orientation.Horizontal)
        self.top_p_slider.setRange(0, 100)
        self.top_p_slider.setValue(80)
        self.top_p_slider.valueChanged.connect(self.update_top_p_label)
        self.style_slider(self.top_p_slider)

        self.top_p_label = QLabel("0.80")
        self.top_p_label.setMinimumWidth(40)
        self.top_p_label.setStyleSheet("color: #495057; font-weight: 500;")

        top_p_layout.addWidget(self.top_p_slider)
        top_p_layout.addWidget(self.top_p_label)

        self.add_form_row(params_layout, "Top-P:", top_p_layout)

        # Help text
        help_label = QLabel(
            "Temperature controls randomness (0.0 = deterministic, 1.0 = very creative).\n"
            "Top-P controls diversity of word selection."
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #6c757d; font-size: 12px; margin-top: 8px;")
        self.add_form_row(params_layout, "", help_label)

        layout.addWidget(params_group)

        # Custom Prompt Group
        prompt_group = self.create_styled_group("Default Prompt")
        prompt_layout = QVBoxLayout(prompt_group)
        prompt_layout.setSpacing(12)

        self.prompt_edit = QTextEdit()
        self.prompt_edit.setMaximumHeight(100)
        self.prompt_edit.setPlaceholderText("Enter the default prompt for AI processing...")
        self.style_input_widget(self.prompt_edit)
        prompt_layout.addWidget(self.prompt_edit)

        # Prompt presets
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Presets:"))

        for text, prompt in [
            ("Professional", "Rephrase this text to be more professional and clear:"),
            ("Casual", "Rephrase this text to be more casual and friendly:"),
            ("Concise", "Make this text more concise while keeping the meaning:")
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, p=prompt: self.set_prompt_preset(p))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    color: #495057;
                    border: 1px solid #ced4da;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
            """)
            preset_layout.addWidget(btn)

        preset_layout.addStretch()
        prompt_layout.addLayout(preset_layout)

        layout.addWidget(prompt_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "AI Configuration")

    def create_behavior_tab(self) -> None:
        """Create the behavior configuration tab."""
        tab = QWidget()
        tab.setStyleSheet("QWidget { background: white; }")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        # Hotkey Group
        hotkey_group = self.create_styled_group("Global Hotkey")
        hotkey_layout = QFormLayout(hotkey_group)
        hotkey_layout.setSpacing(16)

        self.hotkey_edit = QLineEdit()
        self.hotkey_edit.setPlaceholderText("e.g., <ctrl>+<shift>+r")
        self.style_input_widget(self.hotkey_edit)
        self.add_form_row(hotkey_layout, "Hotkey:", self.hotkey_edit)

        hotkey_help = QLabel(
            "Use pynput format: <ctrl>, <alt>, <shift>, <cmd> (macOS)\n"
            "Example: <ctrl>+<shift>+r"
        )
        hotkey_help.setWordWrap(True)
        hotkey_help.setStyleSheet("color: #6c757d; font-size: 12px; margin-top: 8px;")
        self.add_form_row(hotkey_layout, "", hotkey_help)

        layout.addWidget(hotkey_group)

        # Notifications Group
        notify_group = self.create_styled_group("Notifications")
        notify_layout = QFormLayout(notify_group)
        notify_layout.setSpacing(16)

        self.notifications_checkbox = QCheckBox("Show system notifications")
        self.style_checkbox(self.notifications_checkbox)
        self.add_form_row(notify_layout, "", self.notifications_checkbox)

        layout.addWidget(notify_group)

        # Startup Group
        startup_group = self.create_styled_group("Startup")
        startup_layout = QFormLayout(startup_group)
        startup_layout.setSpacing(16)

        self.auto_start_checkbox = QCheckBox("Start with Windows")
        self.style_checkbox(self.auto_start_checkbox)
        self.add_form_row(startup_layout, "", self.auto_start_checkbox)

        layout.addWidget(startup_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "Behavior")

    def create_advanced_tab(self) -> None:
        """Create the advanced configuration tab."""
        tab = QWidget()
        tab.setStyleSheet("QWidget { background: white; }")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        # Performance Group
        perf_group = self.create_styled_group("Performance")
        perf_layout = QFormLayout(perf_group)
        perf_layout.setSpacing(16)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 120)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" seconds")
        self.style_input_widget(self.timeout_spin)
        self.add_form_row(perf_layout, "API Timeout:", self.timeout_spin)

        self.max_length_spin = QSpinBox()
        self.max_length_spin.setRange(100, 50000)
        self.max_length_spin.setValue(5000)
        self.max_length_spin.setSuffix(" characters")
        self.style_input_widget(self.max_length_spin)
        self.add_form_row(perf_layout, "Max Text Length:", self.max_length_spin)

        layout.addWidget(perf_group)

        # Debug Group
        debug_group = self.create_styled_group("Debug")
        debug_layout = QVBoxLayout(debug_group)
        debug_layout.setSpacing(12)

        reset_btn = QPushButton("Reset All Settings")
        reset_btn.clicked.connect(self.reset_settings)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        debug_layout.addWidget(reset_btn)

        layout.addWidget(debug_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "Advanced")

    def create_styled_group(self, title: str) -> QGroupBox:
        """Create a styled group box."""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 600;
                color: #495057;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                background: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px 0 8px;
                background: #f8f9fa;
                color: #495057;
            }
            /* Style form labels within group boxes */
            QGroupBox QLabel {
                color: #495057;
                font-size: 14px;
                font-weight: 500;
                background: transparent;
            }
            /* Global scrollbar styling */
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #ced4da;
                border-radius: 6px;
                margin: 2px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #adb5bd;
            }
            QScrollBar::handle:vertical:pressed {
                background-color: #6c757d;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar:horizontal {
                background-color: #f8f9fa;
                height: 12px;
                border-radius: 6px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background-color: #ced4da;
                border-radius: 6px;
                margin: 2px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #adb5bd;
            }
            QScrollBar::handle:horizontal:pressed {
                background-color: #6c757d;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
        """)
        return group

    def add_form_row(self, layout: QFormLayout, label_text: str, widget) -> None:
        """Add a properly styled form row with label."""
        if label_text:
            label = QLabel(label_text)
            label.setStyleSheet("""
                QLabel {
                    color: #495057;
                    font-size: 14px;
                    font-weight: 500;
                    background: transparent;
                }
            """)
            layout.addRow(label, widget)
        else:
            layout.addRow(widget)

    def style_input_widget(self, widget) -> None:
        """Apply modern styling to input widgets."""
        widget.setStyleSheet("""
            QLineEdit, QComboBox, QSpinBox, QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: white;
                color: #495057;
                selection-background-color: #667eea;
                selection-color: white;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
                border-color: #667eea;
                outline: none;
                background-color: #ffffff;
            }
            /* Improved ComboBox styling */
            QComboBox {
                padding-right: 20px;
                min-height: 18px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #ced4da;
                border-left-style: solid;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background-color: #f8f9fa;
            }
            QComboBox::drop-down:hover {
                background-color: #e9ecef;
            }
            QComboBox::down-arrow {
                image: none;
                border-style: solid;
                border-width: 4px 4px 0px 4px;
                border-color: #6c757d transparent transparent transparent;
                width: 0px;
                height: 0px;
            }
            QComboBox::down-arrow:hover {
                border-top-color: #495057;
            }
            /* ComboBox dropdown list styling */
            QComboBox QAbstractItemView {
                border: 1px solid #ced4da;
                border-radius: 6px;
                background-color: white;
                selection-background-color: #667eea;
                selection-color: white;
                outline: none;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border: none;
                color: #495057;
                min-height: 20px;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #667eea;
                color: white;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e9ecef;
                color: #495057;
                border-radius: 4px;
            }
            /* SpinBox button styling */
            QSpinBox::up-button, QSpinBox::down-button {
                subcontrol-origin: border;
                width: 16px;
                border: none;
                background-color: #f8f9fa;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #e9ecef;
            }
            QSpinBox::up-arrow {
                image: none;
                border-style: solid;
                border-width: 0px 4px 4px 4px;
                border-color: transparent transparent #6c757d transparent;
                width: 0px;
                height: 0px;
            }
            QSpinBox::down-arrow {
                image: none;
                border-style: solid;
                border-width: 4px 4px 0px 4px;
                border-color: #6c757d transparent transparent transparent;
                width: 0px;
                height: 0px;
            }
            /* TextEdit scrollbar styling */
            QTextEdit QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
                border: none;
            }
            QTextEdit QScrollBar::handle:vertical {
                background-color: #ced4da;
                border-radius: 6px;
                margin: 2px;
                min-height: 20px;
            }
            QTextEdit QScrollBar::handle:vertical:hover {
                background-color: #adb5bd;
            }
            QTextEdit QScrollBar::handle:vertical:pressed {
                background-color: #6c757d;
            }
            QTextEdit QScrollBar::add-line:vertical, QTextEdit QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

        # Apply additional global scrollbar styling to the widget
        if hasattr(widget, 'setVerticalScrollBarPolicy'):
            widget.setStyleSheet(widget.styleSheet() + """
                /* Global scrollbar for any scrollable widget */
                QScrollBar:vertical {
                    background-color: #f8f9fa;
                    width: 12px;
                    border-radius: 6px;
                    border: none;
                }
                QScrollBar::handle:vertical {
                    background-color: #ced4da;
                    border-radius: 6px;
                    margin: 2px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #adb5bd;
                }
                QScrollBar::handle:vertical:pressed {
                    background-color: #6c757d;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    border: none;
                    background: none;
                }
            """)

    def style_checkbox(self, checkbox: QCheckBox) -> None:
        """Apply modern styling to checkboxes."""
        checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 8px;
                font-size: 14px;
                color: #495057;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #667eea;
                border-color: #667eea;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #5a6fd8;
                border-color: #5a6fd8;
            }
        """)

    def style_slider(self, slider: QSlider) -> None:
        """Apply modern styling to sliders."""
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #ced4da;
                height: 6px;
                background: #e9ecef;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #667eea;
                border: 2px solid #667eea;
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #5a6fd8;
                border-color: #5a6fd8;
            }
        """)

    # Rest of the implementation methods (load_current_settings, save_settings, etc.)
    # These would be similar to the attachment but adapted for the modern UI

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
        # Set provider selection
        for i in range(self.provider_combo.count()):
            if self.provider_combo.itemData(i) == self.current_settings.api_provider.value:
                self.provider_combo.setCurrentIndex(i)
                break

        # Trigger provider change to update UI
        self.on_provider_changed()

        # API Configuration
        current_api_key = self.current_settings.current_api_key
        if current_api_key:
            self.api_key_edit.setText(current_api_key)

        current_model = self.current_settings.current_model
        self.set_selected_model(current_model)

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

    def save_settings(self) -> None:
        """Save settings and close dialog."""
        try:
            new_settings = self.get_settings_from_ui()

            # Validate settings
            if not new_settings.current_api_key:
                provider_name = "Google AI" if new_settings.api_provider == APIProvider.GOOGLE else "OpenRouter"
                QMessageBox.warning(
                    self,
                    "Missing API Key",
                    f"Please enter your {provider_name} API key."
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

    def get_settings_from_ui(self) -> ChiselSettings:
        """Get settings from UI controls."""
        # Start with current settings to preserve provider-specific data
        new_settings = ChiselSettings(
            # Provider configuration
            api_provider=self.get_current_provider(),

            # Copy all existing provider-specific settings
            google_api_key=self.current_settings.google_api_key,
            google_model=self.current_settings.google_model,
            openrouter_api_key=self.current_settings.openrouter_api_key,
            openrouter_model=self.current_settings.openrouter_model,

            # Legacy fields for compatibility
            api_key=self.current_settings.api_key,
            ai_model=self.current_settings.ai_model,

            # Common settings
            current_prompt=self.prompt_edit.toPlainText().strip(),
            temperature=self.temperature_slider.value() / 100.0,
            top_p=self.top_p_slider.value() / 100.0,
            global_hotkey=self.hotkey_edit.text().strip(),
            show_notifications=self.notifications_checkbox.isChecked(),
            auto_start=self.auto_start_checkbox.isChecked(),
            api_timeout=self.timeout_spin.value(),
            max_text_length=self.max_length_spin.value()
        )

        # Update current provider's API key and model
        api_key = self.api_key_edit.text().strip() or None
        model = self.get_selected_model_name()

        if api_key:
            new_settings.set_current_api_key(api_key)
        new_settings.set_current_model(model)

        return new_settings

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
            "API connection test not yet implemented.\n"
            "This will test your API key in a future version."
        )

    def reset_settings(self) -> None:
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            default_settings = ChiselSettings()
            self.current_settings = default_settings
            self.load_current_settings()
            logger.info("Settings reset to defaults")

    # Additional implementation methods for model handling, provider changes, etc.
    # These would be similar to the attachment implementation

    def populate_fallback_models(self) -> None:
        """Populate combo box with fallback models for current provider."""
        provider = self.get_current_provider()
        if provider == APIProvider.GOOGLE:
            fallback_models = GeminiClient._get_fallback_models_static()
        elif provider == APIProvider.OPENROUTER:
            temp_client = OpenRouterClient("dummy", 10)
            fallback_models = temp_client._get_fallback_models()
        else:
            fallback_models = []

        self.available_models = fallback_models
        self.update_model_combo()

    def get_current_provider(self) -> APIProvider:
        """Get currently selected provider."""
        provider_data = self.provider_combo.currentData()
        if provider_data:
            return APIProvider(provider_data)
        return APIProvider.GOOGLE

    def on_provider_changed(self) -> None:
        """Handle provider selection changes."""
        provider = self.get_current_provider()
        logger.info(f"Provider changed to: {provider.value}")

        # Update API key placeholder and group title
        if provider == APIProvider.GOOGLE:
            self.api_group.setTitle("Google AI Configuration")
            self.api_key_edit.setPlaceholderText("Enter your Google AI API key")
        elif provider == APIProvider.OPENROUTER:
            self.api_group.setTitle("OpenRouter Configuration")
            self.api_key_edit.setPlaceholderText("Enter your OpenRouter API key")

        # Load provider-specific API key if available
        if provider == APIProvider.GOOGLE and self.current_settings.google_api_key:
            self.api_key_edit.setText(self.current_settings.google_api_key)
        elif provider == APIProvider.OPENROUTER and self.current_settings.openrouter_api_key:
            self.api_key_edit.setText(self.current_settings.openrouter_api_key)
        else:
            self.api_key_edit.clear()

        # Clear models and load appropriate ones
        self.model_combo.clear()
        self.populate_fallback_models()

        # Enable/disable refresh button based on API key availability
        has_key = bool(self.api_key_edit.text().strip())
        self.refresh_models_btn.setEnabled(has_key)

        # Auto-fetch models if we have an API key
        if has_key:
            self.fetch_models()

    def update_model_combo(self) -> None:
        """Update the model combo box with available models."""
        current_selection = self.model_combo.currentData()
        if current_selection is None and self.model_combo.count() > 0:
            current_selection = self.model_combo.currentText()

        self.model_combo.clear()

        for model in self.available_models:
            display_text = f"{model.display_name or model.name}"
            if model.description:
                display_text += f" - {model.description[:50]}..."

            self.model_combo.addItem(display_text, model.name)

        # Restore previous selection if available
        if current_selection:
            for i in range(self.model_combo.count()):
                if self.model_combo.itemData(i) == current_selection:
                    self.model_combo.setCurrentIndex(i)
                    return

            # If not found, add it as a custom entry
            self.model_combo.addItem(current_selection, current_selection)
            self.model_combo.setCurrentIndex(self.model_combo.count() - 1)

    def fetch_models(self) -> None:
        """Start fetching models from current provider's API."""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            return

        provider = self.get_current_provider()

        # Stop any existing worker
        if self.model_fetch_worker and self.model_fetch_worker.isRunning():
            self.model_fetch_worker.terminate()
            self.model_fetch_worker.wait()

        # Start new worker with current provider
        self.model_fetch_worker = ModelFetchWorker(provider, api_key)
        self.model_fetch_worker.models_fetched.connect(self.on_models_fetched)
        self.model_fetch_worker.fetch_error.connect(self.on_model_fetch_error)

        # Show loading state
        self.model_loading_label.setText("Loading models...")
        self.model_loading_label.show()
        self.refresh_models_btn.setEnabled(False)

        self.model_fetch_worker.start()

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

        # Show success message briefly
        self.model_loading_label.setText("✓ Models updated")
        self.model_loading_label.setStyleSheet("color: #28a745; font-size: 12px;")
        self.model_loading_label.show()

        # Hide success message after 2 seconds
        QTimer.singleShot(2000, self.model_loading_label.hide)

    def on_model_fetch_error(self, error_message: str) -> None:
        """Handle model fetching error."""
        self.model_loading_label.setText("⚠ Failed to load models")
        self.model_loading_label.setStyleSheet("color: #dc3545; font-size: 12px;")
        self.refresh_models_btn.setEnabled(True)

        # Hide error message after 3 seconds
        QTimer.singleShot(3000, lambda: (
            self.model_loading_label.hide(),
            self.model_loading_label.setStyleSheet("color: #6c757d; font-size: 12px;")
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
        for i in range(self.model_combo.count()):
            item_data = self.model_combo.itemData(i)
            if item_data == model_name:
                self.model_combo.setCurrentIndex(i)
                return

        # If not found, add it as a custom entry
        self.model_combo.addItem(model_name, model_name)
        self.model_combo.setCurrentIndex(self.model_combo.count() - 1)

    def on_api_key_changed(self) -> None:
        """Handle API key changes."""
        # Enable/disable refresh button based on API key availability
        has_key = bool(self.api_key_edit.text().strip())
        self.refresh_models_btn.setEnabled(has_key)

        # Auto-refresh models if we have a valid-looking API key
        api_key = self.api_key_edit.text().strip()
        if len(api_key) > 20:  # Basic validation
            # Delay fetching to avoid too many requests while typing
            if hasattr(self, '_api_key_timer'):
                self._api_key_timer.stop()

            self._api_key_timer = QTimer()
            self._api_key_timer.setSingleShot(True)
            self._api_key_timer.timeout.connect(self.fetch_models)
            self._api_key_timer.start(1000)  # Wait 1 second after typing stops
