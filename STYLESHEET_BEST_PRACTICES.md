# Stylesheet Management Best Practices for Python Projects

This document outlines best practices for managing external stylesheets in Python applications, particularly those using PyQt/PySide frameworks.

## Overview

This project has been refactored to use external stylesheets instead of embedded styles, providing better maintainability, reusability, and separation of concerns.

## Project Structure

```
src/chisel/
├── styles/
│   ├── __init__.py          # Package initialization and exports
│   ├── loader.py            # StylesheetLoader class and utilities
│   └── main.qss             # Main stylesheet file
├── settings_dialog.py       # Uses external stylesheets
├── about_window.py          # Uses external stylesheets
└── ...
```

## Key Components

### 1. StylesheetLoader Class (`styles/loader.py`)

A robust utility class that provides:

- **Caching**: Stylesheets are loaded once and cached for performance
- **Error Handling**: Graceful fallback when stylesheets can't be loaded
- **Hot Reloading**: Development feature to reload stylesheets on changes
- **Component-Specific Loading**: Load specific stylesheets for different components
- **Automatic Path Detection**: Intelligently finds stylesheet files

#### Key Features:

```python
from chisel.styles import StylesheetLoader, apply_main_stylesheet

# Simple usage
apply_main_stylesheet(widget)

# Advanced usage
loader = StylesheetLoader()
stylesheet = loader.load_stylesheet("main.qss")
loader.apply_stylesheet(widget, "main.qss")

# Hot reloading for development
loader.enable_hot_reload()
```

### 2. Stylesheet Organization (`styles/main.qss`)

The main stylesheet is organized by component with clear sections:

- **Global Styles**: Common elements like scrollbars
- **Component-Specific Styles**: Organized by widget class (SettingsDialog, AboutWindow)
- **Object Name Selectors**: Using `setObjectName()` for specific targeting

## Best Practices

### 1. File Organization

#### ✅ Recommended Structure
```
styles/
├── __init__.py              # Package exports
├── loader.py                # Stylesheet management utilities
├── main.qss                 # Primary application stylesheet
├── themes/                  # Optional: Multiple themes
│   ├── dark.qss
│   └── light.qss
└── components/              # Optional: Component-specific styles
    ├── dialogs.qss
    └── buttons.qss
```

#### ❌ Avoid
- Mixing styles with business logic files
- Deeply nested style directories
- Inconsistent naming conventions

### 2. Linking Stylesheets

#### ✅ Recommended Approach
```python
# In your widget class
from .styles import apply_main_stylesheet

class MyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setObjectName("MyDialog")  # Important for CSS targeting
        apply_main_stylesheet(self)     # Apply external styles
        self.setup_ui()
```

#### ❌ Avoid
```python
# Don't use inline styles
self.setStyleSheet("""
    QDialog {
        background-color: #2b2b2b;
        color: #ffffff;
    }
""")
```

### 3. CSS Selector Strategy

#### ✅ Use Object Names for Specificity
```css
/* Target specific instances */
QDialog#SettingsDialog {
    background-color: #2b2b2b;
}

QPushButton#saveButton {
    background-color: #4CAF50;
}
```

#### ✅ Use Class Selectors for Common Styles
```css
/* Apply to all buttons */
QPushButton {
    border-radius: 4px;
    padding: 8px 16px;
}
```

### 4. Performance Optimization

#### ✅ Efficient Loading
- Use caching to avoid repeated file reads
- Load stylesheets once during application startup
- Use lazy loading for optional themes

```python
# Good: Cache and reuse
loader = StylesheetLoader()
stylesheet = loader.load_stylesheet("main.qss")  # Cached after first load

# Apply to multiple widgets efficiently
for widget in widgets:
    loader.apply_stylesheet(widget, "main.qss")  # Uses cached content
```

#### ❌ Avoid
```python
# Bad: Reading file multiple times
for widget in widgets:
    with open("styles/main.qss") as f:
        widget.setStyleSheet(f.read())
```

### 5. Development Workflow

#### Hot Reloading for Development
```python
# Enable during development
if DEBUG:
    loader.enable_hot_reload()
    # Stylesheets will automatically reload when files change
```

#### Testing Stylesheets
```python
# Create test scripts to verify styling
def test_stylesheet_loading():
    loader = StylesheetLoader()
    stylesheet = loader.load_stylesheet("main.qss")
    assert len(stylesheet) > 0
    print(f"✓ Stylesheet loaded ({len(stylesheet)} characters)")
```

### 6. Error Handling

#### ✅ Graceful Degradation
```python
class StylesheetLoader:
    def load_stylesheet(self, filename: str) -> str:
        try:
            # Attempt to load stylesheet
            return self._load_file(filename)
        except FileNotFoundError:
            logger.warning(f"Stylesheet {filename} not found, using defaults")
            return ""  # Graceful fallback
        except Exception as e:
            logger.error(f"Error loading stylesheet {filename}: {e}")
            return ""
```

### 7. Maintenance Guidelines

#### Version Control
- Keep stylesheets in version control
- Use meaningful commit messages for style changes
- Consider separate branches for major theme changes

#### Documentation
- Document custom CSS properties and their purposes
- Maintain a style guide for consistent design
- Comment complex selectors in CSS files

```css
/* Settings Dialog - Main container */
QDialog#SettingsDialog {
    background-color: #2b2b2b;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
}

/* Settings Dialog - Tab styling with hover effects */
QDialog#SettingsDialog QTabBar::tab {
    background-color: #404040;
    color: #cccccc;
    padding: 12px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
```

## Migration Guide

When refactoring from inline styles to external stylesheets:

1. **Extract Styles**: Copy all `setStyleSheet()` calls to a QSS file
2. **Add Object Names**: Use `setObjectName()` for specific targeting
3. **Create Loader**: Implement or use the StylesheetLoader utility
4. **Update Imports**: Import and use the stylesheet application function
5. **Test Thoroughly**: Verify all styling works as expected
6. **Remove Inline Styles**: Clean up old `setStyleSheet()` calls

## Benefits of This Approach

- **Maintainability**: Centralized styling makes updates easier
- **Reusability**: Styles can be shared across components
- **Performance**: Caching reduces file I/O operations
- **Flexibility**: Easy to implement themes and customization
- **Separation of Concerns**: UI logic separated from styling
- **Development Experience**: Hot reloading speeds up design iteration

## Common Pitfalls to Avoid

1. **Forgetting Object Names**: Without `setObjectName()`, specific targeting won't work
2. **CSS Specificity Issues**: Understand how Qt CSS specificity works
3. **File Path Problems**: Use absolute paths or proper relative path resolution
4. **Performance Issues**: Don't reload stylesheets unnecessarily
5. **Error Handling**: Always handle missing or invalid stylesheet files gracefully

## Conclusion

By following these best practices, you can create a maintainable, performant, and flexible styling system for your Python applications. The key is to treat stylesheets as first-class citizens in your codebase, with proper organization, loading mechanisms, and development workflows.