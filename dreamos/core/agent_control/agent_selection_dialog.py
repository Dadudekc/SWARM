"""
Agent Selection Dialog Module

Handles the agent selection dialog UI.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal

from ..ui.theme_manager import ThemeManager

class AgentSelectionDialog(QDialog):
    """Dialog for selecting one or more agents."""
    
    agent_selected = pyqtSignal(list)
    
    def __init__(self, agents: list, parent=None, allow_multiple: bool = False):
        """Initialize the dialog.
        
        Args:
            agents: List of available agent IDs
            parent: Parent widget
            allow_multiple: Whether to allow multiple selection
        """
        super().__init__(parent)
        self.agents = agents
        self.allow_multiple = allow_multiple
        self.selected_agents = []
        
        self.setWindowTitle("Select Agent")
        self.setModal(True)
        self.setMinimumWidth(300)
        
        # Apply theme
        ThemeManager.apply_dialog_theme(self)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # Add label
        label = QLabel("Select agent(s):")
        layout.addWidget(label)
        
        # Add list widget
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(
            QListWidget.MultiSelection if self.allow_multiple else QListWidget.SingleSelection
        )
        
        # Add agents to list
        for agent in self.agents:
            item = QListWidgetItem(f"Agent {agent}")
            item.setData(Qt.UserRole, agent)
            self.list_widget.addItem(item)
            
        layout.addWidget(self.list_widget)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        select_button = QPushButton("Select")
        select_button.clicked.connect(self._handle_selection)
        button_layout.addWidget(select_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def _handle_selection(self):
        """Handle agent selection."""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
            
        self.selected_agents = [item.data(Qt.UserRole) for item in selected_items]
        self.agent_selected.emit(self.selected_agents)
        self.accept() 