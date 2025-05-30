"""
Log Console Module

Provides a UI console for displaying log messages.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QFrame, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QTextCursor

class LogConsole(QFrame):
    """Console widget for displaying log messages."""
    
    def __init__(self, parent=None):
        """Initialize the log console."""
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the console UI."""
        # Set frame style
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
        """)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Log Console")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        layout.addWidget(title)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                border: none;
            }
        """)
        layout.addWidget(self.log_text)
        
    def log(self, message: str, level: str = "info"):
        """Add a log message to the console.
        
        Args:
            message: The message to display
            level: The log level (info, warning, error)
        """
        # Map level to color
        colors = {
            "info": "#cccccc",
            "warning": "#ffcc00",
            "error": "#ff6666"
        }
        color = colors.get(level.lower(), colors["info"])
        
        # Format message with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f'<span style="color: {color}">[{timestamp}] {message}</span><br>'
        
        # Add to console
        self.log_text.append(formatted_message)
        
        # Scroll to bottom
        self.log_text.moveCursor(QTextCursor.End)

        # Replace sipPyTypeDict() with sipPyTypeDictRef()
        # Example: self.setProperty("sipPyTypeDictRef", ...) 