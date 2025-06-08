"""
Agent Monitor Module
------------------
Widget for monitoring agent statuses and operations.
"""

import sys
from datetime import datetime
from typing import Optional, Dict, Any, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

from dreamos.core.autonomy.agent_tools.agent_cellphone import AgentCellphone
from dreamos.core.autonomy.agent_tools.agent_restarter import AgentRestarter
from dreamos.core.autonomy.agent_tools.agent_onboarder import AgentOnboarder
from dreamos.core.utils.core_utils import load_json

class AgentMonitor(QWidget):
    """Widget for monitoring agent statuses."""
    
    # Signal emitted when refresh is requested
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None, cellphone=None):
        """Initialize the agent monitor.
        
        Args:
            parent: Parent widget
            cellphone: Optional AgentCellphone instance for testing
        """
        super().__init__(parent)
        self.cellphone = cellphone
        self._init_ui()
        
        # Setup refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_agents)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
        
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Create refresh button
        refresh_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._on_refresh)
        refresh_layout.addStretch()
        refresh_layout.addWidget(self.refresh_btn)
        layout.addLayout(refresh_layout)
        
        # Create agent status table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Agent ID",
            "Status",
            "Last Update",
            "Uptime"
        ])
        
        # Configure table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Agent ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Last Update
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Uptime
        
        layout.addWidget(self.table)
        
        # Add some placeholder data
        self._add_placeholder_data()
        
    def _add_placeholder_data(self):
        """Add placeholder data to the table."""
        self.table.setRowCount(3)
        
        # Agent 1
        self.table.setItem(0, 0, QTableWidgetItem("AGENT-1"))
        self.table.setItem(0, 1, QTableWidgetItem("Active"))
        self.table.setItem(0, 2, QTableWidgetItem("2025-06-08 17:50:00"))
        self.table.setItem(0, 3, QTableWidgetItem("2h 15m"))
        
        # Agent 2
        self.table.setItem(1, 0, QTableWidgetItem("AGENT-2"))
        self.table.setItem(1, 1, QTableWidgetItem("Standby"))
        self.table.setItem(1, 2, QTableWidgetItem("2025-06-08 17:45:00"))
        self.table.setItem(1, 3, QTableWidgetItem("1h 30m"))
        
        # Agent 3
        self.table.setItem(2, 0, QTableWidgetItem("AGENT-3"))
        self.table.setItem(2, 1, QTableWidgetItem("Error"))
        self.table.setItem(2, 2, QTableWidgetItem("2025-06-08 17:40:00"))
        self.table.setItem(2, 3, QTableWidgetItem("45m"))
        
    def refresh_agents(self):
        """Refresh the agent display."""
        try:
            # Load status
            status_file = self.restarter.status_file
            if not status_file.exists():
                return
                
            status = load_json(status_file)
            
            # Update table
            self.table.setRowCount(len(status))
            for i, (agent_id, agent_status) in enumerate(status.items()):
                self.table.setItem(i, 0, QTableWidgetItem(agent_id))
                self.table.setItem(i, 1, QTableWidgetItem(
                    "Active" if agent_status.get("is_active", False) else "Inactive"
                ))
                self.table.setItem(i, 2, QTableWidgetItem(
                    agent_status.get("last_active", "Never")
                ))
                self.table.setItem(i, 3, QTableWidgetItem(
                    agent_status.get("uptime", "Unknown")
                ))
                
                # Store agent ID
                self.table.item(i, 0).setData(Qt.UserRole, agent_id)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error refreshing agents: {e}")
            
    def _show_devlog(self):
        """Show devlog for selected agent."""
        selected = self.table.selectedItems()
        if not selected:
            return
            
        # Get agent ID
        agent_id = selected[0].data(Qt.UserRole)
        if not agent_id:
            return
            
        try:
            # Load devlog
            devlog_file = self.restarter.runtime_dir / "devlog" / "agents" / agent_id / "devlog.md"
            if devlog_file.exists():
                self.devlog_text.setText(devlog_file.read_text())
            else:
                self.devlog_text.setText("No devlog available")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading devlog: {e}")
            
    def _force_resume(self):
        """Force resume selected agent."""
        agent_id = self.agent_combo.currentText()
        if not agent_id:
            return
            
        try:
            success = self.restarter.controller.force_resume(agent_id)
            if success:
                QMessageBox.information(self, "Success", f"Resumed agent {agent_id}")
            else:
                QMessageBox.warning(self, "Warning", f"Failed to resume agent {agent_id}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error resuming agent: {e}")
            
    def _onboard_agent(self):
        """Onboard selected agent."""
        agent_id = self.agent_combo.currentText()
        if not agent_id:
            return
            
        try:
            success = self.onboarder.onboard_agent(agent_id, force=True)
            if success:
                QMessageBox.information(self, "Success", f"Onboarded agent {agent_id}")
            else:
                QMessageBox.warning(self, "Warning", f"Failed to onboard agent {agent_id}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error onboarding agent: {e}")
            
    def _on_refresh(self):
        """Handle refresh button click."""
        self.refresh_requested.emit()
        # TODO: Implement actual refresh logic
        
    def closeEvent(self, event):
        """Handle widget close event."""
        self.refresh_timer.stop()
        super().closeEvent(event)

    def update_agent_status(self, agent_id: str, status: str, last_update: str, uptime: str):
        """Update the status of an agent in the table.
        
        Args:
            agent_id: ID of the agent
            status: Current status
            last_update: Timestamp of last update
            uptime: Agent uptime
        """
        # Find agent row
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == agent_id:
                self.table.setItem(row, 1, QTableWidgetItem(status))
                self.table.setItem(row, 2, QTableWidgetItem(last_update))
                self.table.setItem(row, 3, QTableWidgetItem(uptime))
                return
        
        # Agent not found, add new row
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(agent_id))
        self.table.setItem(row, 1, QTableWidgetItem(status))
        self.table.setItem(row, 2, QTableWidgetItem(last_update))
        self.table.setItem(row, 3, QTableWidgetItem(uptime)) 