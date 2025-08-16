# Chisel - AI-Powered Text Rephrasing Tool

Chisel is a desktop background utility that enables AI-powered text rephrasing with global hotkey support. Select any text and press `Ctrl+Shift+R` to instantly rephrase it using your chosen AI provider.

## Features

- **Global Hotkey**: Works across all applications with `Ctrl+Shift+R`
- **Multiple AI Providers**: Supports Google Gemini and OpenRouter
- **Customizable Models**: Choose from a wide range of AI models
- **Background Operation**: Runs invisibly in system tray
- **Cross-Platform**: Windows, macOS, and Linux support
- **Secure**: API keys stored in system keyring
- **Reliable**: Robust error handling and clipboard management

## Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/chisel/chisel.git
   cd chisel
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. **Get an API key**
   - For **Google Gemini**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - For **OpenRouter**: Visit [OpenRouter.ai](https://openrouter.ai/keys)

2. **Run Chisel**
   ```bash
   python -m chisel
   ```

3. **Configure the API key**
   - Right-click the system tray icon
   - Select "Settings..."
   - Choose your AI provider (Google Gemini or OpenRouter)
   - Enter your API key
   - Select your preferred AI model
   - Customize the rephrasing prompt if desired

### Usage

1. **Select text** in any application (Word, browser, code editor, etc.)
2. **Press `Ctrl+Shift+R`** to trigger rephrasing
3. **The text will be automatically replaced** with the AI-rephrased version

## Development

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run in development mode
python -m chisel --dev

# Run tests
pytest

# Code formatting
black src/
isort src/

# Type checking
mypy src/chisel/
```

### Building

```bash
# Build standalone executable
pyinstaller --onefile --windowed --icon=resources/icons/chisel.ico src/chisel/__main__.py
```

## Architecture

- **app.py** - Main application controller, orchestrates all components
- **hotkey.py** - Cross-platform global hotkey management
- **processor.py** - Text capture and processing workflow
- **ai_client.py** - Integration with AI providers (Google Gemini, OpenRouter)
- **settings.py** - Configuration management with secure storage
- **tray.py** - System tray interface
- **clipboard.py** - Safe clipboard operations

## Platform Notes

### Windows
- May require administrator privileges for some applications
- Includes Windows-specific optimizations

### macOS
- Requires accessibility permissions for global hotkeys
- Install with: `pip install PyObjC`

### Linux
- X11/Wayland compatibility
- May need additional system packages

## Configuration

Settings are stored in:
- **Windows**: `%APPDATA%\Chisel\settings.json`
- **macOS**: `~/Library/Application Support/Chisel/settings.json`
- **Linux**: `~/.config/chisel/settings.json`

API keys are securely stored in the system keyring.

## Troubleshooting

### Global hotkey not working
- Try running as administrator (Windows)
- Check accessibility permissions (macOS)
- Verify X11 support (Linux)

### API errors
- Verify API key is correct
- Check internet connection
- Monitor API usage limits

### Text not captured
- Ensure text is actually selected
- Try different applications
- Check clipboard permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- Report issues on [GitHub Issues](https://github.com/chisel/chisel/issues)
- Read the [documentation](https://chisel.readthedocs.io)
- Join our [community discussions](https://github.com/chisel/chisel/discussions)
