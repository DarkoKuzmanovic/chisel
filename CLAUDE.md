# Chisel - AI-Powered Text Rephrasing Tool

## Project Overview

Chisel is a desktop background utility for AI-powered text rephrasing with global hotkey support. Built with Python 3.11+ and PyQt6, it runs invisibly in the system tray and allows users to rephrase selected text using Ctrl+Shift+R across any application.

**Core Workflow**: Select text → Press hotkey → Text automatically rephrased in place using Google Gemini API

## Technology Stack

- **Language**: Python 3.11+
- **GUI Framework**: PyQt6
- **AI API**: Google Gemini API
- **Global Hotkeys**: pynput library
- **HTTP Client**: httpx (async)
- **Settings Storage**: keyring (secure) + JSON files
- **Packaging**: PyInstaller

## Architecture

### Core Components

1. **app.py** - Main application controller and PyQt6 app lifecycle
2. **hotkey.py** - Cross-platform global hotkey registration (Ctrl+Shift+R)
3. **processor.py** - Text processing workflow (capture → AI → replace)
4. **ai_client.py** - Google Gemini API integration with error handling
5. **settings.py** - Configuration management with secure API key storage
6. **tray.py** - System tray interface for background operation
7. **clipboard.py** - Safe clipboard operations with backup/restore

### Key Technical Challenges

- **Cross-platform hotkey registration** - Works on Windows, macOS, Linux
- **Robust text capture** - Copy simulation with retry logic and timing
- **Safe clipboard handling** - Backup original clipboard, restore on errors
- **Background operation** - No persistent UI windows, system tray only
- **Error recovery** - Never break user workflow, transparent error handling

## Development Commands

```bash
# Setup virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements-dev.txt

# Run in development mode
python -m chisel.app --dev

# Run tests
pytest tests/

# Build executable
python scripts/build.py
```

## Project Structure

```
chisel/
├── src/
│   └── chisel/
│       ├── __init__.py
│       ├── app.py              # Main application controller
│       ├── hotkey.py           # Global hotkey manager
│       ├── processor.py        # Text processing workflow
│       ├── ai_client.py        # Gemini API integration
│       ├── settings.py         # Configuration management
│       ├── tray.py             # System tray interface
│       ├── clipboard.py        # Clipboard operations
│       └── utils.py            # Utility functions
├── resources/
│   ├── icons/                  # Application icons
│   └── ui/                     # Qt UI files
├── tests/
├── scripts/
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── README.md
```

## Development Guidelines

### Code Standards
- Use async/await for I/O operations (API calls, file operations)
- Follow PEP 8 style guidelines
- Type hints required for all function signatures
- Comprehensive error handling with user-friendly messages
- Logging with loguru for debugging

### Error Handling Strategy
- **Never break user workflow** - Restore clipboard on any failure
- **Graceful degradation** - Show notifications for errors, continue running
- **Retry logic** - Text capture and API calls with exponential backoff
- **Timeout protection** - All network requests must have timeouts

### Security Requirements
- API keys stored in system keyring (never plaintext files)
- Input sanitization before API calls
- Certificate verification for HTTPS requests
- Minimal permissions required

### Testing Approach
- Unit tests for all core components
- Integration tests for end-to-end workflow
- Manual testing across different applications
- Cross-platform compatibility validation

## API Integration

### Google Gemini API
- Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent`
- Authentication: API key in query parameter
- Default timeout: 30 seconds
- Response format: JSON with candidates array

### Default Prompt
```
Rephrase this text to be more professional and clear:
```

## Build & Distribution

### Development Build
```bash
python -m chisel.app --dev
```

### Production Build
```bash
# Windows executable
pyinstaller --onefile --windowed --icon=resources/icons/chisel.ico src/chisel/app.py

# Create installer with NSIS
python scripts/package.py --platform windows
```

## Performance Targets

- **Memory usage**: < 50MB during idle
- **CPU usage**: < 5% during processing  
- **API response**: < 3 seconds average
- **Startup time**: < 2 seconds
- **Uptime**: 24+ hours without restart

## Success Metrics

- Global hotkey works in 95% of applications
- Text capture success rate > 98%
- Zero data loss incidents (clipboard restore)
- Processing workflow feels instant to user

## Development Notes

### Platform Considerations
- **Windows**: May need admin privileges for global hotkeys in some apps
- **macOS**: Requires accessibility permissions for text capture
- **Linux**: X11/Wayland compatibility for hotkeys

### Common Issues
- Timing sensitive - text capture needs proper delays
- Clipboard conflicts with other applications
- Antivirus may flag global hotkey registration
- Some applications have protected text fields

## Getting Started

1. Set up development environment with Python 3.11+
2. Install dependencies from requirements-dev.txt  
3. Get Google Gemini API key from Google AI Studio
4. Run `python -m chisel.app --dev` to start in development mode
5. Configure API key in settings UI
6. Test with Ctrl+Shift+R in any text application

## Useful Resources

- [Google Gemini API Docs](https://ai.google.dev/gemini-api/docs)
- [PyQt6 Documentation](https://doc.qt.io/qtforpython-6/)
- [pynput Documentation](https://pynput.readthedocs.io/)
- [PyInstaller Manual](https://pyinstaller.org/en/stable/)