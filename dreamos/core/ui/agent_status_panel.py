"""
Agent Status Panel Module

Provides a UI panel for displaying agent status information.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class AgentStatusPanel(QFrame):
    """Panel for displaying agent status information."""
    
    def __init__(self, parent=None):
        """Initialize the status panel."""
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the panel UI."""
        # Set frame style
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
        """)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Agent Status")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        layout.addWidget(title)
        
        # Status content
        self.status_label = QLabel("No agents connected")
        self.status_label.setStyleSheet("color: #cccccc;")
        layout.addWidget(self.status_label)
        
        # Add stretch to push content to top
        layout.addStretch()
        
    def update_status(self, status_text: str):
        """Update the status display.
        
        Args:
            status_text: The status text to display
        """
        self.status_label.setText(status_text)
        self.setProperty("sipPyTypeDictRef", status_text) 