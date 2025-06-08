"""
Main Window Module
----------------
Primary application window for Dream.OS.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QAction, QMenuBar, QStatusBar
)
from PyQt5.QtCore import Qt

from .agent_monitor import AgentMonitor

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, cellphone=None):
        """Initialize the main window.
        
        Args:
            cellphone: Optional AgentCellphone instance for testing
        """
        super().__init__()
        self.cellphone = cellphone
        self.setWindowTitle("Dream.OS Control Panel")
        self.setWindowFlags(Qt.Window)
        self.setMinimumSize(800, 600)
        
        # Initialize UI components
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Add agent monitor tab
        self.agent_monitor = AgentMonitor(cellphone=self.cellphone)
        self.tabs.addTab(self.agent_monitor, "Agents")
        
        # Add logs tab placeholder
        self.tabs.addTab(QWidget(), "Logs")
        
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
        refresh_agents_action.triggered.connect(self.agent_monitor._on_refresh)
        view_menu.addAction(refresh_agents_action)
        
        # Help menu
        help_menu = self.menuBar().addMenu("Help")
