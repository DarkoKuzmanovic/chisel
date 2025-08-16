"""
About window for Chisel application.

Displays application information, version, and links.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap, QFont, QDesktopServices
from pathlib import Path
from loguru import logger


class AboutWindow(QDialog):
    """About window for the Chisel application."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("About Chisel")
        self.setModal(True)
        self.setFixedSize(380, 320)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #2c3e50;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton#linkButton {
                background-color: transparent;
                color: #3498db;
                text-decoration: underline;
                padding: 4px 8px;
                font-weight: normal;
            }
            QPushButton#linkButton:hover {
                color: #2980b9;
            }
        """)

        self.setup_ui()

        logger.info("About window initialized")

    def setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # --- Header ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        # Icon
        icon_label = QLabel()
        icon_path = Path("resources/icons/chisel_tray.png")
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path)).scaled(
                72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            icon_label.setPixmap(pixmap)
            icon_label.setStyleSheet("""
                QLabel {
                    border-radius: 12px;
                    background-color: #f8f9fa;
                    padding: 8px;
                }
            """)
        header_layout.addWidget(icon_label)

        # Title section
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        title_label = QLabel("Chisel")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_font.setFamily("Segoe UI")
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50;")

        version_label = QLabel("v1.0.0")
        version_font = QFont()
        version_font.setPointSize(11)
        version_label.setFont(version_font)
        version_label.setStyleSheet("color: #7f8c8d;")

        tagline_label = QLabel("AI-Powered Text Rephrasing")
        tagline_font = QFont()
        tagline_font.setPointSize(10)
        tagline_label.setFont(tagline_font)
        tagline_label.setStyleSheet("color: #95a5a6;")

        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        title_layout.addWidget(tagline_label)
        title_layout.addStretch()

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # --- Separator ---
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                min-height: 1px;
                max-height: 1px;
            }
        """)
        layout.addWidget(separator)

        # --- Description ---
        description_label = QLabel(
            "Chisel is an intelligent text rephrasing tool that works seamlessly "
            "in the background. Simply select any text and use the global hotkey "
            "to instantly rephrase it with AI assistance."
        )
        description_label.setWordWrap(True)
        description_font = QFont()
        description_font.setPointSize(10)
        description_label.setFont(description_font)
        description_label.setStyleSheet("color: #34495e; line-height: 1.4;")
        layout.addWidget(description_label)

        # --- Author Info ---
        author_layout = QVBoxLayout()
        author_layout.setSpacing(8)

        author_label = QLabel("Created by Darko Kuzmanovic")
        author_font = QFont()
        author_font.setPointSize(10)
        author_font.setBold(True)
        author_label.setFont(author_font)
        author_label.setStyleSheet("color: #2c3e50;")
        author_layout.addWidget(author_label)

        # GitHub link
        github_button = QPushButton("View on GitHub")
        github_button.setObjectName("linkButton")
        github_button.setCursor(Qt.CursorShape.PointingHandCursor)
        github_button.clicked.connect(self.open_github)
        author_layout.addWidget(github_button)

        layout.addLayout(author_layout)
        layout.addStretch()

        # --- Footer ---
        footer_layout = QHBoxLayout()

        # Copyright
        copyright_label = QLabel("© 2025 Darko Kuzmanovic")
        copyright_font = QFont()
        copyright_font.setPointSize(9)
        copyright_label.setFont(copyright_font)
        copyright_label.setStyleSheet("color: #95a5a6;")
        footer_layout.addWidget(copyright_label)

        footer_layout.addStretch()

        # Close button
        close_button = QPushButton("Close")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.accept)
        close_button.setDefault(True)
        footer_layout.addWidget(close_button)

        layout.addLayout(footer_layout)

    def open_github(self):
        """Open the GitHub repository in the default browser."""
        QDesktopServices.openUrl(QUrl("https://github.com/DarkoKuzmanovic/chisel"))
        logger.info("GitHub link clicked - opening repository")

