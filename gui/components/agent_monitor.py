"""
Agent Monitor Component
---------------------
GUI component for monitoring and controlling agents.
"""

import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Set
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox,
    QMenu, QDialog, QProgressBar, QCheckBox,
    QFormLayout, QLineEdit, QFileDialog,
    QFrame, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject, QSize
from PyQt5.QtGui import QColor, QCursor, QPainter, QPainterPath, QBrush, QPen

from dreamos.core.autonomy.agent_tools.agent_cellphone import AgentCellphone
from dreamos.core.autonomy.agent_tools.agent_restarter import AgentRestarter
from dreamos.core.autonomy.agent_tools.agent_onboarder import AgentOnboarder
from dreamos.core.telemetry.ws_client import WSClient
from dreamos.core.utils.json_utils import load_json

# ---------------------------------------------------------------------
#  Dataclass Config
# ---------------------------------------------------------------------
@dataclass
class OnboardingOptions:
    agent_id: str
    use_ui_automation: bool
    force: bool
    startup_prompt: Optional[str] = None
    episode_file: Optional[Path] = None
    discord_notify: bool = False

# ---------------------------------------------------------------------
#  Worker Thread
# ---------------------------------------------------------------------
class _OnboardWorker(QObject):
    finished = pyqtSignal(bool, str)          # success, msg
    progress = pyqtSignal(int)                # 0–100
    stage = pyqtSignal(str, int)              # stage name, percent
    
    def __init__(self, onboarder, opts: OnboardingOptions):
        super().__init__()
        self._onboarder = onboarder
        self._opts = opts

    def run(self) -> None:
        try:
            # Pre-check
            self.stage.emit("pre-check", 10)
            if not self._onboarder.validate_agent(self._opts.agent_id):
                raise ValueError(f"Invalid agent ID: {self._opts.agent_id}")
                
            # Prepare directories
            self.stage.emit("prepare-dirs", 20)
            success = self._onboarder.prepare_agent(
                self._opts.agent_id,
                self._opts.startup_prompt,
                self._opts.episode_file
            )
            
            # Launch Cursor
            self.stage.emit("launch-cursor", 40)
            if self._opts.use_ui_automation:
                success &= self._onboarder.launch_cursor(self._opts.agent_id)
                
            # Send prompt
            self.stage.emit("send-prompt", 60)
            success &= self._onboarder.onboard_agent(
                self._opts.agent_id,
                ui_automation=self._opts.use_ui_automation,
                force=self._opts.force
            )
            
            # Verify heartbeat
            self.stage.emit("verify-heartbeat", 80)
            if success:
                success &= self._onboarder.verify_heartbeat(self._opts.agent_id)
                
            # Post-hooks
            self.stage.emit("post-hooks", 90)
            if success and self._opts.discord_notify:
                from dreamos.core.messaging.discord import DiscordNotifier
                DiscordNotifier.notify(f"✅ Agent *{self._opts.agent_id}* onboarded.")
                
            self.stage.emit("complete", 100)
            self.finished.emit(success, "Onboarding complete." if success else "Onboarding failed.")
            
        except Exception as exc:
            self.finished.emit(False, f"Error: {exc}")

# ---------------------------------------------------------------------
#  Glass Dialog
# ---------------------------------------------------------------------
class GlassDialog(QDialog):
    """Frameless dialog with glass effect."""
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Main frame
        frame = QFrame(self)
        frame.setObjectName("glassFrame")
        frame.setStyleSheet("""
            #glassFrame {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
        """)
        
        # Add frame to layout
        layout.addWidget(frame)
        
    def paintEvent(self, event):
        """Paint the glass effect."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create path for rounded corners
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 10, 10)
        
        # Fill with semi-transparent white
        painter.fillPath(path, QBrush(QColor(255, 255, 255, 230)))
        
        # Draw border
        painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
        painter.drawPath(path)

# ---------------------------------------------------------------------
#  Dialog
# ---------------------------------------------------------------------
class OnboardingDialog(GlassDialog):
    completed = pyqtSignal()   # emitted on *any* finish
    
    def __init__(self, parent, agent_onboarder):
        super().__init__(parent)
        self.setWindowTitle("Agent Onboarding")
        self._onboarder = agent_onboarder
        self._ws_client = WSClient()
        self._ws_client.heartbeat.connect(self._on_live_status)
        self._ws_client.start()
        self._setup_ui()
        self._wire()
        
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        vbox = QVBoxLayout(self)
        form = QFormLayout()
        
        # Agent ID selection
        self.cmb_agent = QComboBox()
        self.cmb_agent.setEditable(True)
        self.cmb_agent.addItems([f"agent-{i+1}" for i in range(8)])
        form.addRow("Agent ID:", self.cmb_agent)
        
        # Batch mode
        self.chk_batch = QCheckBox("Batch Mode")
        self.chk_batch.stateChanged.connect(self._toggle_batch_mode)
        form.addRow(self.chk_batch)
        
        # Batch input (hidden by default)
        self.txt_batch = QTextEdit()
        self.txt_batch.setPlaceholderText("Enter agent IDs (one per line)")
        self.txt_batch.setMaximumHeight(100)
        self.txt_batch.hide()
        form.addRow(self.txt_batch)
        
        # Options
        self.chk_ui = QCheckBox("UI Automation")
        self.chk_force = QCheckBox("Force onboarding")
        form.addRow(self.chk_ui, self.chk_force)
        
        # Startup prompt
        self.txt_prompt = QLineEdit()
        form.addRow("Startup Prompt:", self.txt_prompt)
        
        # Episode selection
        self.lbl_episode = QLabel("<i>No episode selected</i>")
        btn_episode = QPushButton("Choose Episode…")
        ep_row = QHBoxLayout()
        ep_row.addWidget(self.lbl_episode)
        ep_row.addWidget(btn_episode)
        form.addRow("Episode Task:", ep_row)
        
        # Discord notification
        self.chk_discord = QCheckBox("Discord notify when done")
        form.addRow(self.chk_discord)
        
        vbox.addLayout(form)
        
        # Progress area
        self.progress_area = QScrollArea()
        self.progress_area.setWidgetResizable(True)
        self.progress_area.setMaximumHeight(200)
        self.progress_widget = QWidget()
        self.progress_layout = QVBoxLayout(self.progress_widget)
        self.progress_area.setWidget(self.progress_widget)
        vbox.addWidget(self.progress_area)
        
        # Buttons
        h = QHBoxLayout()
        self.btn_ok = QPushButton("Onboard")
        self.btn_cancel = QPushButton("Cancel")
        h.addStretch(1)
        h.addWidget(self.btn_ok)
        h.addWidget(self.btn_cancel)
        vbox.addLayout(h)
        
        self._btn_episode = btn_episode
        self.resize(460, 400)
        
    def _wire(self):
        """Wire up signals and slots."""
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self._begin_onboard)
        self._btn_episode.clicked.connect(self._choose_episode)
        
    def _toggle_batch_mode(self, state):
        """Toggle batch mode UI elements."""
        self.txt_batch.setVisible(state == Qt.Checked)
        self.cmb_agent.setVisible(state != Qt.Checked)
        
    def _choose_episode(self):
        """Open file dialog to choose episode YAML."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Episode YAML",
            str(Path("config/episodes").absolute()),
            "YAML Files (*.yaml *.yml)"
        )
        if path:
            self.lbl_episode.setText(Path(path).name)
            self.lbl_episode.setToolTip(path)
            
    def _collect_options(self) -> List[OnboardingOptions]:
        """Collect all options from UI."""
        if self.chk_batch.isChecked():
            # Get agent IDs from batch input
            agent_ids = [
                line.strip()
                for line in self.txt_batch.toPlainText().splitlines()
                if line.strip()
            ]
        else:
            agent_ids = [self.cmb_agent.currentText().strip()]
            
        return [
            OnboardingOptions(
                agent_id=agent_id,
                use_ui_automation=self.chk_ui.isChecked(),
                force=self.chk_force.isChecked(),
                startup_prompt=self.txt_prompt.text().strip() or None,
                episode_file=Path(self.lbl_episode.toolTip()) if self.lbl_episode.toolTip() else None,
                discord_notify=self.chk_discord.isChecked()
            )
            for agent_id in agent_ids
        ]
        
    def _begin_onboard(self):
        """Start the onboarding process."""
        options_list = self._collect_options()
        if not options_list:
            QMessageBox.warning(self, "Input Error", "No agent IDs specified.")
            return
            
        # Disable UI
        self.btn_ok.setEnabled(False)
        self.progress_layout.clear()
        
        # Create progress bars for each agent
        self.progress_bars = {}
        for opts in options_list:
            # Create progress widget
            widget = QWidget()
            layout = QVBoxLayout(widget)
            
            # Agent label
            label = QLabel(f"Onboarding {opts.agent_id}...")
            layout.addWidget(label)
            
            # Progress bar
            progress = QProgressBar()
            progress.setAlignment(Qt.AlignCenter)
            layout.addWidget(progress)
            
            # Status label
            status = QLabel("Initializing...")
            layout.addWidget(status)
            
            # Add to progress area
            self.progress_layout.addWidget(widget)
            
            # Store references
            self.progress_bars[opts.agent_id] = {
                "label": label,
                "progress": progress,
                "status": status
            }
            
        # Start workers
        self.workers = []
        for opts in options_list:
            worker = _OnboardWorker(self._onboarder, opts)
            worker.progress.connect(
                lambda p, aid=opts.agent_id: self._update_progress(aid, p)
            )
            worker.stage.connect(
                lambda s, p, aid=opts.agent_id: self._update_stage(aid, s, p)
            )
            worker.finished.connect(
                lambda s, m, aid=opts.agent_id: self._on_worker_finished(aid, s, m)
            )
            self.workers.append(worker)
            
            # Start worker
            thread = QThread(self)
            worker.moveToThread(thread)
            thread.started.connect(worker.run)
            thread.start()
            
    def _update_progress(self, agent_id: str, value: int):
        """Update progress bar for an agent."""
        if agent_id in self.progress_bars:
            self.progress_bars[agent_id]["progress"].setValue(value)
            
    def _update_stage(self, agent_id: str, stage: str, percent: int):
        """Update stage status for an agent."""
        if agent_id in self.progress_bars:
            self.progress_bars[agent_id]["status"].setText(f"{stage} ({percent}%)")
            
    def _on_worker_finished(self, agent_id: str, success: bool, msg: str):
        """Handle worker completion."""
        if agent_id in self.progress_bars:
            bar = self.progress_bars[agent_id]
            if success:
                bar["label"].setText(f"✅ {agent_id} onboarded")
                bar["status"].setText("Complete")
            else:
                bar["label"].setText(f"❌ {agent_id} failed")
                bar["status"].setText(msg)
                
        # Check if all workers are done
        if all(w.isFinished() for w in self.workers):
            self.btn_ok.setEnabled(True)
            self.completed.emit()
            
    def _on_live_status(self, data: Dict[str, Any]):
        """Handle live status updates."""
        agent_id = data.get("agent")
        if not agent_id or agent_id not in self.progress_bars:
            return
            
        status = data.get("status", "unknown")
        bar = self.progress_bars[agent_id]
        
        # Update status with heartbeat
        if status == "active":
            bar["status"].setText("Active (heartbeat received)")
            
    def closeEvent(self, event):
        """Handle dialog close."""
        self._ws_client.stop()
        super().closeEvent(event)

class AgentMonitor(QWidget):
    """GUI component for monitoring and controlling agents."""
    
    def __init__(self, parent: Optional[QWidget] = None, cellphone: Optional[AgentCellphone] = None):
        """Initialize the agent monitor.
        
        Args:
            parent: Optional parent widget
            cellphone: Optional AgentCellphone instance for agent coordinates
        """
        super().__init__(parent)
        
        # Initialize tools with optional cellphone
        self.cellphone = cellphone or AgentCellphone()
        self.restarter = AgentRestarter()
        self.onboarder = AgentOnboarder()
        
        # Setup UI
        self._setup_ui()
        
        # Setup refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_agents)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
        
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout()
        
        # Controls
        controls = QHBoxLayout()
        
        # Agent selector
        self.agent_combo = QComboBox()
        self.agent_combo.addItems(self.cellphone.coords.keys())
        controls.addWidget(QLabel("Agent:"))
        controls.addWidget(self.agent_combo)
        
        # Action buttons
        resume_btn = QPushButton("Force Resume")
        resume_btn.clicked.connect(self._force_resume)
        controls.addWidget(resume_btn)
        
        onboard_btn = QPushButton("Onboard")
        onboard_btn.clicked.connect(self._onboard_agent)
        controls.addWidget(onboard_btn)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_agents)
        controls.addWidget(refresh_btn)
        
        layout.addLayout(controls)
        
        # Agent table
        self.agent_table = QTableWidget()
        self.agent_table.setColumnCount(5)
        self.agent_table.setHorizontalHeaderLabels([
            "Agent ID", "Status", "Last Active", "Topic", "Stalled"
        ])
        self.agent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.agent_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.agent_table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.agent_table)
        
        # Devlog view
        self.devlog_text = QTextEdit()
        self.devlog_text.setReadOnly(True)
        self.devlog_text.setMaximumHeight(200)
        layout.addWidget(QLabel("Devlog:"))
        layout.addWidget(self.devlog_text)
        
        # Connect table selection
        self.agent_table.itemSelectionChanged.connect(self._show_devlog)
        
        self.setLayout(layout)
        
    def refresh_agents(self):
        """Refresh the agent display."""
        try:
            # Load status
            status_file = self.restarter.status_file
            if not status_file.exists():
                return
                
            status = load_json(status_file)
            
            # Update table
            self.agent_table.setRowCount(len(status))
            for i, (agent_id, agent_status) in enumerate(status.items()):
                # Set agent ID
                id_item = QTableWidgetItem(agent_id)
                id_item.setData(Qt.UserRole, agent_id)
                self.agent_table.setItem(i, 0, id_item)
                
                # Set status with color
                status_text = "Active" if agent_status.get("is_active", False) else "Inactive"
                status_item = QTableWidgetItem(status_text)
                if status_text == "Active":
                    status_item.setBackground(QColor(200, 255, 200))  # Light green
                elif status_text == "Inactive":
                    status_item.setBackground(QColor(255, 200, 200))  # Light red
                self.agent_table.setItem(i, 1, status_item)
                
                # Set last active
                last_active = agent_status.get("last_active", "Never")
                last_active_item = QTableWidgetItem(last_active)
                self.agent_table.setItem(i, 2, last_active_item)
                
                # Set topics
                topics = ", ".join(self.restarter.agent_topics.get(agent_id, []))
                self.agent_table.setItem(i, 3, QTableWidgetItem(topics))
                
                # Set stalled status with color
                is_stalled = agent_status.get("is_stalled", False)
                stalled_item = QTableWidgetItem("Yes" if is_stalled else "No")
                if is_stalled:
                    stalled_item.setBackground(QColor(255, 255, 200))  # Light yellow
                self.agent_table.setItem(i, 4, stalled_item)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error refreshing agents: {e}")
            
    def _show_devlog(self):
        """Show devlog for selected agent."""
        selected = self.agent_table.selectedItems()
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
        """Show onboarding dialog."""
        dialog = OnboardingDialog(self, self.onboarder)
        dialog.completed.connect(self.refresh_agents)
        dialog.exec_()
            
    def _show_context_menu(self, position):
        """Show context menu for agent table."""
        # Get selected row
        row = self.agent_table.rowAt(position.y())
        if row < 0:
            return
            
        # Get agent ID
        agent_id = self.agent_table.item(row, 0).data(Qt.UserRole)
        if not agent_id:
            return
            
        # Create menu
        menu = QMenu()
        
        # Add actions
        view_logs_action = menu.addAction("🔍 View Devlog")
        resume_action = menu.addAction("🔁 Resume Agent")
        clear_errors_action = menu.addAction("🧹 Clear Errors")
        
        # Show menu and get selected action
        action = menu.exec_(QCursor.pos())
        
        if action == view_logs_action:
            self._show_devlog_modal(agent_id)
        elif action == resume_action:
            self._force_resume_agent(agent_id)
        elif action == clear_errors_action:
            self._clear_agent_errors(agent_id)
            
    def _show_devlog_modal(self, agent_id: str):
        """Show devlog in a modal dialog."""
        try:
            # Load devlog
            devlog_file = self.restarter.runtime_dir / "devlog" / "agents" / agent_id / "devlog.md"
            if not devlog_file.exists():
                QMessageBox.warning(self, "Warning", f"No devlog available for agent {agent_id}")
                return
                
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Devlog - {agent_id}")
            dialog.setModal(True)
            dialog.setMinimumSize(800, 600)
            
            # Add text widget
            layout = QVBoxLayout()
            text = QTextEdit()
            text.setReadOnly(True)
            text.setText(devlog_file.read_text())
            layout.addWidget(text)
            
            # Add close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)
            
            dialog.setLayout(layout)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error showing devlog: {e}")
            
    def _force_resume_agent(self, agent_id: str):
        """Force resume a specific agent."""
        try:
            success = self.restarter.controller.force_resume(agent_id)
            if success:
                QMessageBox.information(self, "Success", f"Resumed agent {agent_id}")
                self.refresh_agents()  # Refresh display
            else:
                QMessageBox.warning(self, "Warning", f"Failed to resume agent {agent_id}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error resuming agent: {e}")
            
    def _clear_agent_errors(self, agent_id: str):
        """Clear error state for an agent."""
        try:
            # Get error file path
            error_file = self.restarter.runtime_dir / "errors" / f"{agent_id}.json"
            
            if error_file.exists():
                error_file.unlink()  # Delete error file
                QMessageBox.information(self, "Success", f"Cleared errors for agent {agent_id}")
                self.refresh_agents()  # Refresh display
            else:
                QMessageBox.information(self, "Info", f"No errors found for agent {agent_id}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error clearing agent errors: {e}")
            
    def closeEvent(self, event):
        """Handle widget close event."""
        self.refresh_timer.stop()
        super().closeEvent(event) 