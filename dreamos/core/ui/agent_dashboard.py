"""
Agent Dashboard Module

Main GUI dashboard for monitoring and controlling agents.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QTextEdit,
    QComboBox, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

from ..utils.agent_status import AgentStatus
from ..agent_control.agent_operations import AgentOperations
from ..agent_control.agent_restarter import AgentRestarter
from ..agent_control.agent_onboarder import AgentOnboarder
from .agent_status_panel import AgentStatusPanel

logger = logging.getLogger(__name__)

class AgentDashboard(QMainWindow):
    """Main dashboard window for agent monitoring and control."""
    
    def __init__(self, 
                 agent_ops: AgentOperations,
                 agent_restarter: AgentRestarter,
                 agent_onboarder: AgentOnboarder):
        """Initialize the dashboard.
        
        Args:
            agent_ops: Agent operations instance
            agent_restarter: Agent restarter instance
            agent_onboarder: Agent onboarder instance
        """
        super().__init__()
        self.agent_ops = agent_ops
        self.agent_restarter = agent_restarter
        self.agent_onboarder = agent_onboarder
        
        self.setWindowTitle("Dream.OS Agent Dashboard")
        self.setMinimumSize(1200, 800)
        
        # Set up UI
        self._setup_ui()
        
        # Start update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(1000)  # Update every second
        
    def _setup_ui(self):
        """Set up the dashboard UI."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Agent Status Tab
        status_tab = QWidget()
        status_layout = QVBoxLayout(status_tab)
        
        # Status panels container
        self.status_panels = {}
        status_scroll = QScrollArea()
        status_scroll.setWidgetResizable(True)
        status_scroll.setFrameStyle(QFrame.NoFrame)
        
        status_container = QWidget()
        self.status_container_layout = QVBoxLayout(status_container)
        status_scroll.setWidget(status_container)
        
        status_layout.addWidget(status_scroll)
        tabs.addTab(status_tab, "Agent Status")
        
        # Devlog Tab
        devlog_tab = QWidget()
        devlog_layout = QVBoxLayout(devlog_tab)
        
        self.devlog = QTextEdit()
        self.devlog.setReadOnly(True)
        self.devlog.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        
        devlog_layout.addWidget(self.devlog)
        tabs.addTab(devlog_tab, "Devlog")
        
        # Control Tab
        control_tab = QWidget()
        control_layout = QVBoxLayout(control_tab)
        
        # Agent selection
        agent_select_layout = QHBoxLayout()
        agent_select_layout.addWidget(QLabel("Select Agent:"))
        
        self.agent_selector = QComboBox()
        self.agent_selector.setMinimumWidth(200)
        agent_select_layout.addWidget(self.agent_selector)
        
        control_layout.addLayout(agent_select_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.resume_button = QPushButton("Resume Agent")
        self.resume_button.clicked.connect(self._resume_agent)
        button_layout.addWidget(self.resume_button)
        
        self.restart_button = QPushButton("Restart Agent")
        self.restart_button.clicked.connect(self._restart_agent)
        button_layout.addWidget(self.restart_button)
        
        self.onboard_button = QPushButton("Onboard Agent")
        self.onboard_button.clicked.connect(self._onboard_agent)
        button_layout.addWidget(self.onboard_button)
        
        control_layout.addLayout(button_layout)
        control_layout.addStretch()
        
        tabs.addTab(control_tab, "Control")
        
    async def _update_status(self):
        """Update agent status displays."""
        try:
            # Get all agent statuses
            statuses = await self.agent_ops.get_all_agent_statuses()
            
            # Update agent selector
            current_agents = set(self.status_panels.keys())
            new_agents = set(statuses.keys())
            
            # Remove old agents
            for agent_id in current_agents - new_agents:
                if agent_id in self.status_panels:
                    self.status_container_layout.removeWidget(self.status_panels[agent_id])
                    self.status_panels[agent_id].deleteLater()
                    del self.status_panels[agent_id]
                    
            # Add new agents
            for agent_id in new_agents - current_agents:
                panel = AgentStatusPanel()
                self.status_panels[agent_id] = panel
                self.status_container_layout.addWidget(panel)
                self.agent_selector.addItem(agent_id)
                
            # Update all panels
            for agent_id, status in statuses.items():
                if agent_id in self.status_panels:
                    self.status_panels[agent_id].update_status(
                        f"Status: {status.get('status', 'unknown')}\n"
                        f"Last Active: {status.get('last_active', 'never')}\n"
                        f"Current Step: {status.get('current_step', 'none')}"
                    )
                    
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            
    async def _resume_agent(self):
        """Resume selected agent."""
        try:
            agent_id = self.agent_selector.currentText()
            if not agent_id:
                return
                
            success = await self.agent_ops.resume_agent(agent_id)
            if success:
                self._log_message(f"Successfully resumed agent {agent_id}")
            else:
                self._log_message(f"Failed to resume agent {agent_id}")
                
        except Exception as e:
            logger.error(f"Error resuming agent: {e}")
            
    async def _restart_agent(self):
        """Restart selected agent."""
        try:
            agent_id = self.agent_selector.currentText()
            if not agent_id:
                return
                
            await self.agent_restarter._handle_stalled_agent(agent_id)
            self._log_message(f"Restart initiated for agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Error restarting agent: {e}")
            
    async def _onboard_agent(self):
        """Onboard selected agent."""
        try:
            agent_id = self.agent_selector.currentText()
            if not agent_id:
                return
                
            success = await self.agent_onboarder.onboard_agent(agent_id)
            if success:
                self._log_message(f"Successfully onboarded agent {agent_id}")
            else:
                self._log_message(f"Failed to onboard agent {agent_id}")
                
        except Exception as e:
            logger.error(f"Error onboarding agent: {e}")
            
    def _log_message(self, message: str):
        """Add message to devlog.
        
        Args:
            message: Message to log
        """
        self.devlog.append(f"[{datetime.now().isoformat()}] {message}") 