# Chisel - Python/PyQt Project Specification

## 🎯 Project Overview

**Name**: Chisel - AI-Powered Text Rephrasing Tool  
**Technology Stack**: Python 3.11+ with PyQt6  
**Target Platforms**: Windows, macOS, Linux  
**Purpose**: Desktop background utility for AI-powered text rephrasing with global hotkey support

## 📋 Core Requirements

### **Primary Functionality**
1. **Global Hotkey**: System-wide keyboard shortcut (Ctrl+Shift+R) that works across all applications
2. **Text Capture**: Automatically copy selected text using keyboard simulation
3. **AI Processing**: Send captured text to Google Gemini API for rephrasing
4. **Text Replacement**: Paste processed text back, replacing the original selection
5. **Background Operation**: Run invisibly in system tray, no persistent UI window

### **User Experience Goals**
- **Seamless Workflow**: Select text → Press hotkey → Text automatically rephrased in place
- **Minimal Setup**: Configure API key and prompt once, then forget about it
- **Reliable Operation**: Robust error handling that never breaks user workflow
- **Cross-Application**: Works in any text field (Word, browsers, code editors, etc.)

## 🏗️ Technical Architecture

### **Core Components**

#### **1. Application Controller** (`app.py`)
```python
class ChiselApp(QApplication):
    """Main application controller"""
    - Initialize system tray
    - Register global hotkey
    - Coordinate all components
    - Handle application lifecycle
```

#### **2. Global Hotkey Manager** (`hotkey.py`)
```python
class GlobalHotkeyManager:
    """Cross-platform global hotkey registration"""
    - Register system-wide keyboard shortcuts
    - Handle hotkey events
    - Platform-specific implementations
```

#### **3. Text Processor** (`processor.py`)
```python
class TextProcessor:
    """Core text processing workflow"""
    - Capture selected text (copy simulation)
    - Send to AI API for processing
    - Handle clipboard operations safely
    - Retry logic and error recovery
```

#### **4. AI API Client** (`ai_client.py`)
```python
class GeminiClient:
    """Google Gemini API integration"""
    - Format requests for Gemini API
    - Handle API responses and errors
    - Timeout and rate limiting
```

#### **5. Settings Manager** (`settings.py`)
```python
class SettingsManager:
    """Configuration persistence"""
    - Load/save user settings
    - API key secure storage
    - Default prompts and preferences
```

#### **6. System Tray Interface** (`tray.py`)
```python
class SystemTrayIcon(QSystemTrayIcon):
    """System tray integration"""
    - Background operation
    - Settings access
    - Status indication
```

## 📦 Required Dependencies

### **Core Libraries**
```bash
# GUI Framework
PyQt6>=6.6.0

# Global hotkey support
pynput>=1.7.6          # Cross-platform input simulation and monitoring
keyboard>=0.13.5       # Alternative hotkey library (Windows/Linux)

# HTTP requests
requests>=2.31.0       # API communication
httpx>=0.25.0         # Alternative async HTTP client

# System integration  
psutil>=5.9.0         # Process management
pywin32>=306          # Windows-specific APIs (Windows only)
plyer>=2.1.0          # Cross-platform notifications

# Configuration
pydantic>=2.5.0       # Settings validation
keyring>=24.3.0       # Secure credential storage

# Logging
loguru>=0.7.0         # Enhanced logging

# Packaging
pyinstaller>=6.3.0    # Standalone executable creation
```

### **Platform-Specific Libraries**
```bash
# Windows
pywin32>=306                    # Windows APIs
windows-curses>=2.3.0          # Console handling

# macOS  
PyObjC>=10.1                   # macOS system integration
rumps>=0.4.0                   # macOS menu bar apps

# Linux
python3-dev                    # Development headers
libxcb-xinerama0              # X11 support
```

## 🗂️ Project Structure

```
chisel-python/
├── src/
│   ├── chisel/
│   │   ├── __init__.py
│   │   ├── app.py              # Main application controller
│   │   ├── hotkey.py           # Global hotkey manager
│   │   ├── processor.py        # Text processing workflow
│   │   ├── ai_client.py        # Gemini API integration
│   │   ├── settings.py         # Configuration management
│   │   ├── tray.py             # System tray interface
│   │   ├── clipboard.py        # Clipboard operations
│   │   └── utils.py            # Utility functions
│   └── resources/
│       ├── icons/              # Application icons
│       ├── ui/                 # Qt UI files (.ui)
│       └── styles/             # CSS stylesheets
├── tests/
│   ├── test_hotkey.py
│   ├── test_processor.py
│   ├── test_ai_client.py
│   └── test_settings.py
├── scripts/
│   ├── build.py                # Build automation
│   ├── package.py              # Distribution packaging
│   └── install.py              # Installation script
├── docs/
│   ├── API.md                  # API documentation
│   ├── DEVELOPMENT.md          # Developer guide
│   └── USER_GUIDE.md           # End-user documentation
├── requirements.txt            # Dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml             # Project metadata
├── setup.py                   # Package setup
└── README.md                  # Project overview
```

## 🔧 Implementation Details

### **1. Global Hotkey Implementation**

#### **Cross-Platform Approach**
```python
# hotkey.py
import platform
from pynput import keyboard
from typing import Callable

class GlobalHotkeyManager:
    def __init__(self):
        self.listeners = []
        self.hotkey_callbacks = {}
        
    def register_hotkey(self, keys: str, callback: Callable):
        """Register a global hotkey"""
        try:
            hotkey = keyboard.GlobalHotKeys({
                keys: callback
            })
            hotkey.start()
            self.listeners.append(hotkey)
            return True
        except Exception as e:
            print(f"Failed to register hotkey: {e}")
            return False
            
    def unregister_all(self):
        """Clean up all hotkey listeners"""
        for listener in self.listeners:
            listener.stop()
        self.listeners.clear()
```

#### **Platform-Specific Considerations**
```python
# Windows: Use win32 APIs for more reliable hotkey detection
# macOS: Accessibility permissions required
# Linux: X11/Wayland compatibility
```

### **2. Text Processing Workflow**

#### **Robust Text Capture**
```python
# processor.py
import time
import pyperclip
from pynput import keyboard
from typing import Optional

class TextProcessor:
    def __init__(self, ai_client, settings):
        self.ai_client = ai_client
        self.settings = settings
        self.keyboard = keyboard.Controller()
        
    async def process_selected_text(self) -> bool:
        """Main text processing workflow"""
        # 1. Backup current clipboard
        original_clipboard = self.get_clipboard_safely()
        
        try:
            # 2. Copy selected text with retries
            selected_text = await self.capture_selected_text()
            if not selected_text:
                self.show_notification("No text selected")
                return False
                
            # 3. Process with AI
            processed_text = await self.ai_client.process_text(
                text=selected_text,
                prompt=self.settings.current_prompt
            )
            
            # 4. Replace original text
            pyperclip.copy(processed_text)
            self.simulate_paste()
            
            self.show_notification("Text rephrased successfully!")
            return True
            
        except Exception as e:
            # 5. Restore original clipboard on error
            if original_clipboard:
                pyperclip.copy(original_clipboard)
            self.show_notification(f"Error: {str(e)}")
            return False
    
    async def capture_selected_text(self) -> Optional[str]:
        """Capture selected text with retry logic"""
        max_retries = 3
        base_delay = 0.1
        
        for attempt in range(max_retries):
            # Simulate Ctrl+C
            self.keyboard.press(keyboard.Key.ctrl)
            self.keyboard.press('c')
            self.keyboard.release('c')
            self.keyboard.release(keyboard.Key.ctrl)
            
            # Wait with increasing delay
            await asyncio.sleep(base_delay * (attempt + 1))
            
            # Check if clipboard changed
            new_clipboard = self.get_clipboard_safely()
            if new_clipboard and new_clipboard.strip():
                return new_clipboard
                
        return None
```

### **3. AI API Integration**

#### **Google Gemini Client**
```python
# ai_client.py
import httpx
import json
from typing import Optional
from dataclasses import dataclass

@dataclass
class AIResponse:
    success: bool
    text: Optional[str] = None
    error: Optional[str] = None

class GeminiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-1.5-pro-latest"
        
    async def process_text(self, text: str, prompt: str) -> str:
        """Send text to Gemini API for processing"""
        
        request_data = {
            "contents": [{
                "parts": [{
                    "text": f"{prompt}\n\nText to process: {text}"
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 500
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/models/{self.model}:generateContent",
                    params={"key": self.api_key},
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extract response text
                processed_text = (
                    data["candidates"][0]["content"]["parts"][0]["text"]
                    if data.get("candidates") else "No response from AI"
                )
                
                return processed_text.strip()
                
            except httpx.TimeoutException:
                raise Exception("AI request timed out")
            except httpx.HTTPStatusError as e:
                raise Exception(f"AI API error: {e.response.status_code}")
            except (KeyError, IndexError):
                raise Exception("Invalid response format from AI")
```

### **4. Settings Management**

#### **Secure Configuration**
```python
# settings.py
import json
import keyring
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional

class ChiselSettings(BaseModel):
    """Application settings with validation"""
    
    # API Configuration
    api_key: Optional[str] = None
    current_prompt: str = Field(
        default="Rephrase this text to be more professional and clear:",
        description="Default prompt for AI processing"
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

class SettingsManager:
    def __init__(self):
        self.app_name = "Chisel"
        self.config_dir = Path.home() / ".chisel"
        self.config_file = self.config_dir / "settings.json"
        self.config_dir.mkdir(exist_ok=True)
        
    def load_settings(self) -> ChiselSettings:
        """Load settings from file and keyring"""
        settings = ChiselSettings()
        
        # Load from config file
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                settings = ChiselSettings(**data)
            except Exception as e:
                print(f"Error loading settings: {e}")
        
        # Load API key from secure storage
        try:
            api_key = keyring.get_password(self.app_name, "api_key")
            if api_key:
                settings.api_key = api_key
        except Exception as e:
            print(f"Error loading API key: {e}")
            
        return settings
    
    def save_settings(self, settings: ChiselSettings):
        """Save settings to file and keyring"""
        # Save API key securely
        if settings.api_key:
            try:
                keyring.set_password(self.app_name, "api_key", settings.api_key)
            except Exception as e:
                print(f"Error saving API key: {e}")
        
        # Save other settings to file
        settings_dict = settings.dict(exclude={"api_key"})
        try:
            with open(self.config_file, 'w') as f:
                json.dump(settings_dict, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
```

### **5. System Tray Integration**

#### **Background Operation**
```python
# tray.py
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal

class SystemTrayIcon(QSystemTrayIcon):
    """System tray icon with menu"""
    
    settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create tray icon
        self.setIcon(QIcon("resources/icons/chisel_tray.png"))
        self.setToolTip("Chisel - AI Text Rephrasing")
        
        # Create context menu
        self.menu = QMenu()
        
        # Settings action
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        self.menu.addAction(settings_action)
        
        self.menu.addSeparator()
        
        # Status action
        self.status_action = QAction("Ready", self)
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)
        
        self.menu.addSeparator()
        
        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(quit_action)
        
        self.setContextMenu(self.menu)
        
        # Handle tray icon activation
        self.activated.connect(self.on_tray_activated)
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.settings_requested.emit()
    
    def update_status(self, status: str):
        """Update status display"""
        self.status_action.setText(status)
        self.setToolTip(f"Chisel - {status}")
    
    def show_message(self, title: str, message: str):
        """Show system notification"""
        self.showMessage(
            title, 
            message, 
            QSystemTrayIcon.MessageIcon.Information, 
            3000
        )
```

## 🚀 Development Roadmap

### **Phase 1: Core Foundation** (Week 1-2)
1. **Project Setup**
   - Initialize Python project structure
   - Configure dependencies and virtual environment
   - Set up development tools (linting, testing)

2. **Basic Components**
   - Implement settings management
   - Create system tray interface
   - Build configuration UI

3. **Text Processing Core**
   - Clipboard operations
   - Keyboard simulation
   - Basic text capture workflow

### **Phase 2: AI Integration** (Week 3)
1. **API Client**
   - Google Gemini API integration
   - Error handling and retries
   - Response processing

2. **Workflow Integration**
   - Connect text capture to AI processing
   - Implement text replacement
   - Add user notifications

### **Phase 3: Global Hotkey** (Week 4)
1. **Hotkey Implementation**
   - Cross-platform hotkey registration
   - Event handling
   - Platform-specific optimizations

2. **Integration Testing**
   - End-to-end workflow testing
   - Error handling validation
   - Performance optimization

### **Phase 4: Polish & Distribution** (Week 5-6)
1. **User Experience**
   - Settings validation
   - Error messages
   - Status indicators

2. **Packaging**
   - PyInstaller configuration
   - Platform-specific installers
   - Auto-update mechanism

## ⚙️ Build & Distribution

### **Development Setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Run in development mode
python -m chisel.app --dev
```

### **Building Executables**
```bash
# Windows
pyinstaller --onefile --windowed --icon=resources/icons/chisel.ico src/chisel/app.py

# macOS
pyinstaller --onefile --windowed --icon=resources/icons/chisel.icns src/chisel/app.py

# Linux
pyinstaller --onefile --windowed src/chisel/app.py
```

### **Installation Packages**
- **Windows**: NSIS installer (.exe)
- **macOS**: DMG with app bundle
- **Linux**: AppImage or Debian package

## 🔒 Security Considerations

### **API Key Storage**
- Use system keyring for secure storage
- Never store keys in plaintext files
- Support key rotation

### **Process Isolation**
- Run with minimal required permissions
- Validate all external inputs
- Secure clipboard handling

### **Network Security**
- Certificate pinning for API requests
- Request timeout and rate limiting
- Input sanitization before API calls

## 🧪 Testing Strategy

### **Unit Tests**
- Settings management
- API client functionality
- Text processing logic
- Clipboard operations

### **Integration Tests**
- End-to-end workflow
- Error handling scenarios
- Cross-platform compatibility

### **Manual Testing**
- Hotkey registration across applications
- Clipboard state management
- System tray interaction

## 📊 Success Metrics

### **Functionality**
- ✅ Global hotkey works in 95% of applications
- ✅ Text capture success rate > 98%
- ✅ API response time < 3 seconds average
- ✅ Zero data loss incidents (clipboard restore)

### **User Experience**
- ✅ One-time setup process < 2 minutes
- ✅ Processing workflow feels instant to user
- ✅ Error recovery is transparent
- ✅ Runs reliably for 24+ hours without restart

### **Technical**
- ✅ Memory usage < 50MB during idle
- ✅ CPU usage < 5% during processing
- ✅ Startup time < 2 seconds
- ✅ Works across Windows, macOS, Linux

---

## 💡 Why Python/PyQt Over Tauri?

### **Advantages**
1. **Mature Ecosystem**: Rich libraries for system integration
2. **Cross-Platform**: Better global hotkey support across platforms
3. **Rapid Development**: Faster iteration and debugging
4. **System Integration**: Native OS APIs easier to access
5. **Deployment**: Familiar packaging and distribution tools

### **Libraries Specifically Suited for This Task**
- **pynput**: Excellent cross-platform input monitoring and simulation
- **keyring**: Secure credential storage across all platforms
- **PyQt6**: Mature, stable GUI framework with system tray support
- **httpx**: Modern HTTP client with async support
- **pyinstaller**: Reliable executable packaging

This specification provides a complete roadmap for building a robust, cross-platform text rephrasing tool that addresses all the complexities discovered in the Tauri version while leveraging Python's ecosystem advantages.