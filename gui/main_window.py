"""
Main Window
----------
Main application window for the GUI.
"""

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QAction, QMenuBar, QStatusBar
)
from PyQt5.QtCore import Qt
from .components.log_monitor import LogMonitor
from .components.agent_monitor import AgentMonitor

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        self.setWindowTitle("Dream.OS Control Panel")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Add agent monitor tab
        self.agent_monitor = AgentMonitor()
        self.tabs.addTab(self.agent_monitor, "Agents")
        
        # Add log monitor tab
        self.log_monitor = LogMonitor()
        self.tabs.addTab(self.log_monitor, "Logs")
        
        # Setup menu bar
        self._setup_menu()
        
        # Setup status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
    def _setup_menu(self):
        """Set up the menu bar."""
        # File menu
        file_menu = self.menuBar().addMenu("File")
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = self.menuBar().addMenu("View")
        
        refresh_agents_action = QAction("Refresh Agents", self)
        refresh_agents_action.triggered.connect(self.agent_monitor.refresh_agents)
        view_menu.addAction(refresh_agents_action)
        
        refresh_logs_action = QAction("Refresh Logs", self)
        refresh_logs_action.triggered.connect(self.log_monitor.refresh_logs)
        view_menu.addAction(refresh_logs_action)
        
        # Help menu
        help_menu = self.menuBar().addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _show_about(self):
        """Show about dialog."""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "About Dream.OS",
            "Dream.OS Control Panel\n\n"
            "A comprehensive monitoring and control interface for the Dream.OS system."
        )
        
    def closeEvent(self, event):
        """Handle window close event."""
        # Cleanup
        self.agent_monitor.close()
        self.log_monitor.close()
        super().closeEvent(event) 
