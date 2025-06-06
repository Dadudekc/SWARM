"""
Log Monitor Component
--------------------
GUI component for monitoring and displaying logs.
"""

import sys
from datetime import datetime
from typing import Optional, Dict, Any, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer
from social.utils.log_manager import LogManager
from dreamos.core.config.config_manager import ConfigManager

class LogMonitor(QWidget):
    """GUI component for monitoring and displaying logs."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the log monitor.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        
        # Initialize LogManager
        log_config = ConfigManager(
            log_dir="logs/gui",
            batch_size=10,
            batch_timeout=0.5,
            max_retries=2,
            retry_delay=0.1
        )
        self.log_manager = LogManager(config=log_config)
        
        # Setup UI
        self._setup_ui()
        
        # Setup refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_logs)
        self.refresh_timer.start(1000)  # Refresh every second
        
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout()
        
        # Controls
        controls = QHBoxLayout()
        
        # Platform selector
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["All", "agent_loop", "social", "devlog", "discord"])
        self.platform_combo.currentTextChanged.connect(self.refresh_logs)
        controls.addWidget(QLabel("Platform:"))
        controls.addWidget(self.platform_combo)
        
        # Level selector
        self.level_combo = QComboBox()
        self.level_combo.addItems(["All", "INFO", "WARNING", "ERROR", "DEBUG"])
        self.level_combo.currentTextChanged.connect(self.refresh_logs)
        controls.addWidget(QLabel("Level:"))
        controls.addWidget(self.level_combo)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_logs)
        controls.addWidget(refresh_btn)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_logs)
        controls.addWidget(clear_btn)
        
        layout.addLayout(controls)
        
        # Log table
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(5)
        self.log_table.setHorizontalHeaderLabels([
            "Timestamp", "Platform", "Level", "Status", "Message"
        ])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.log_table)
        
        # Details view
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        layout.addWidget(self.details_text)
        
        # Connect table selection
        self.log_table.itemSelectionChanged.connect(self._show_details)
        
        self.setLayout(layout)
        
    def refresh_logs(self):
        """Refresh the log display."""
        try:
            # Get filter values
            platform = self.platform_combo.currentText()
            level = self.level_combo.currentText()
            
            # Get logs
            logs = self.log_manager.read_logs(
                platform=platform if platform != "All" else None,
                level=level if level != "All" else None,
                limit=100  # Show last 100 logs
            )
            
            # Update table
            self.log_table.setRowCount(len(logs))
            for i, log in enumerate(reversed(logs)):  # Show newest first
                self.log_table.setItem(i, 0, QTableWidgetItem(log.get("timestamp", "")))
                self.log_table.setItem(i, 1, QTableWidgetItem(log.get("platform", "")))
                self.log_table.setItem(i, 2, QTableWidgetItem(log.get("level", "")))
                self.log_table.setItem(i, 3, QTableWidgetItem(log.get("status", "")))
                self.log_table.setItem(i, 4, QTableWidgetItem(log.get("message", "")))
                
                # Store full log data
                self.log_table.item(i, 0).setData(Qt.UserRole, log)
                
        except Exception as e:
            self.log_manager.error(
                platform="gui",
                status="error",
                message="Error refreshing logs",
                error=str(e)
            )
            
    def clear_logs(self):
        """Clear the log display."""
        self.log_table.setRowCount(0)
        self.details_text.clear()
        
    def _show_details(self):
        """Show details for selected log entry."""
        selected = self.log_table.selectedItems()
        if not selected:
            return
            
        # Get log data
        log = selected[0].data(Qt.UserRole)
        if not log:
            return
            
        # Format details
        details = []
        details.append(f"Timestamp: {log.get('timestamp', '')}")
        details.append(f"Platform: {log.get('platform', '')}")
        details.append(f"Level: {log.get('level', '')}")
        details.append(f"Status: {log.get('status', '')}")
        details.append(f"Message: {log.get('message', '')}")
        
        # Add metadata if present
        if "metadata" in log:
            details.append("\nMetadata:")
            for key, value in log["metadata"].items():
                details.append(f"  {key}: {value}")
                
        # Add error if present
        if "error" in log:
            details.append("\nError:")
            details.append(f"  {log['error']}")
            
        self.details_text.setText("\n".join(details))
        
    def closeEvent(self, event):
        """Handle widget close event."""
        self.refresh_timer.stop()
        super().closeEvent(event) 