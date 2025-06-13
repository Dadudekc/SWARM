"""
Agent Restarter Module

Handles agent recovery and restart operations, including heartbeat monitoring,
retry logic, and cooldown periods. Uses keyboard shortcuts and coordinates to
restart agent conversations.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

import pyautogui
import win32gui
import win32con
import win32process
import psutil

from dreamos.core.agent_control.agent_operations import AgentOperations
from dreamos.core.agent_control.agent_status import AgentStatus

logger = logging.getLogger(__name__)

class AgentRestarter:
    """Handles agent recovery and restart operations."""
    
    def __init__(self,
                 agent_ops: AgentOperations,
                 agent_status: AgentStatus,
                 config: Optional[Dict] = None):
        """Initialize the agent restarter.
        
        Args:
            agent_ops: Agent operations interface
            agent_status: Agent status tracker
            config: Optional configuration dictionary
        """
        self.agent_ops = agent_ops
        self.agent_status = agent_status
        self.config = config or {}
        
        # Recovery settings
        self.heartbeat_timeout = self.config.get('heartbeat_timeout', 300)  # 5 minutes
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_cooldown = self.config.get('retry_cooldown', 60)  # 1 minute
        self.restart_cooldown = self.config.get('restart_cooldown', 300)  # 5 minutes
        
        # Cursor-specific settings
        self.cursor_window_class = "Chrome_WidgetWin_1"  # Cursor's window class
        self.idle_threshold = self.config.get('idle_threshold', 1800)  # 30 minutes
        self.last_activity: Dict[str, float] = {}
        
        # Timing configuration
        self.timing = {
            'delay_after_ctrl_n': self.config.get('delay_after_ctrl_n', 0.5),
            'delay_after_click': self.config.get('delay_after_click', 0.3),
            'delay_between_keys': self.config.get('delay_between_keys', 0.02),
            'delay_after_window_activate': self.config.get('delay_after_window_activate', 0.5)
        }
        
        # Coordinate management
        self.coords_file = Path('config/cursor_agent_coords.json')
        self.input_coords: Dict[str, Tuple[int, int]] = {}
        
        # State tracking
        self._retry_counts: Dict[str, int] = {}
        self._last_restart: Dict[str, float] = {}
        self._monitoring = False
        self._monitor_task = None
        
    async def initialize(self) -> bool:
        """Initialize the restarter.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Reset state
            self._retry_counts.clear()
            self._last_restart.clear()
            self.last_activity.clear()
            
            # Create recovery directory if needed
            recovery_dir = os.path.join(os.getcwd(), 'recovery')
            os.makedirs(recovery_dir, exist_ok=True)
            
            # Load coordinates
            await self._load_coordinates()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize agent restarter: {e}")
            return False
            
    async def _load_coordinates(self) -> None:
        """Load agent coordinates from config file."""
        try:
            if not self.coords_file.exists():
                logger.warning(f"Coordinates file not found: {self.coords_file}")
                return
                
            with open(self.coords_file, 'r') as f:
                coords_data = json.load(f)
                
            for agent_id, coords in coords_data.items():
                if isinstance(coords, (list, tuple)) and len(coords) == 2:
                    self.input_coords[agent_id] = tuple(coords)
                else:
                    logger.warning(f"Invalid coordinates for agent {agent_id}: {coords}")
                    
        except Exception as e:
            logger.error(f"Error loading coordinates: {e}")
            
    async def _get_initial_prompt(self, agent_id: str, resume_reason: str) -> str:
        """Get initial prompt for an agent.
        
        Args:
            agent_id: ID of the agent
            resume_reason: Reason for resuming the agent
            
        Returns:
            str: Initial prompt text
        """
        try:
            # Try to load from file first
            prompt_file = Path(f'config/initial_prompts/agent-{agent_id}.txt')
            if prompt_file.exists():
                with open(prompt_file, 'r') as f:
                    prompt = f.read().strip()
            else:
                # Fallback to default
                prompt = self.config.get('default_initial_prompt', 
                    "Hello, I am ready to assist you. Previous session was interrupted due to {resume_reason}.")
                    
            # Apply substitutions
            prompt = prompt.format(
                agent_id=agent_id,
                resume_reason=resume_reason
            )
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error getting initial prompt for agent {agent_id}: {e}")
            return "Hello, I am ready to assist you."
            
    async def _find_cursor_window(self, agent_id: str) -> Optional[int]:
        """Find the Cursor window for a specific agent.
        
        Args:
            agent_id: ID of the agent to find window for
            
        Returns:
            Optional[int]: Window handle if found, None otherwise
        """
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                class_name = win32gui.GetClassName(hwnd)
                if class_name == self.cursor_window_class:
                    # Get window title
                    title = win32gui.GetWindowText(hwnd)
                    # Check if title contains agent ID
                    if agent_id in title:
                        windows.append(hwnd)
            return True
            
        windows = []
        win32gui.EnumWindows(callback, windows)
        return windows[0] if windows else None
        
    async def _check_cursor_idle(self, agent_id: str) -> bool:
        """Check if a Cursor window is idle.
        
        Args:
            agent_id: ID of the agent to check
            
        Returns:
            bool: True if window is idle
        """
        try:
            hwnd = await self._find_cursor_window(agent_id)
            if not hwnd:
                return False
                
            # Get process ID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if not pid:
                return False
                
            # Get process
            process = psutil.Process(pid)
            
            # Check if process is responding
            if not process.is_running():
                return True
                
            # Check last activity time
            last_active = self.last_activity.get(agent_id, 0)
            if time.time() - last_active > self.idle_threshold:
                return True
                
            # Check if window is minimized
            if win32gui.IsIconic(hwnd):
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking Cursor idle state for agent {agent_id}: {e}")
            return False
            
    async def _restart_conversation(self, agent_id: str, resume_reason: str = "timeout") -> bool:
        """Restart a conversation for an agent using keyboard shortcuts.
        
        Args:
            agent_id: ID of the agent to restart
            resume_reason: Reason for resuming the agent
            
        Returns:
            bool: True if restart successful
        """
        try:
            # Find window
            hwnd = await self._find_cursor_window(agent_id)
            if not hwnd:
                logger.error(f"Could not find Cursor window for agent {agent_id}")
                return False
                
            # Activate window
            win32gui.SetForegroundWindow(hwnd)
            await asyncio.sleep(self.timing['delay_after_window_activate'])
            
            # Start new conversation (Ctrl+N)
            pyautogui.hotkey('ctrl', 'n')
            await asyncio.sleep(self.timing['delay_after_ctrl_n'])
            
            # Get input coordinates for this agent
            coords = self.input_coords.get(agent_id)
            if not coords:
                logger.error(f"No input coordinates configured for agent {agent_id}")
                return False
                
            # Click input field
            pyautogui.click(coords[0], coords[1])
            await asyncio.sleep(self.timing['delay_after_click'])
            
            # Get and type initial prompt
            initial_prompt = await self._get_initial_prompt(agent_id, resume_reason)
            
            # Type with configured delay between keys
            for char in initial_prompt:
                pyautogui.write(char)
                await asyncio.sleep(self.timing['delay_between_keys'])
                
            # Send message (Enter)
            pyautogui.press('enter')
            
            return True
            
        except Exception as e:
            logger.error(f"Error restarting conversation for agent {agent_id}: {e}")
            return False
            
    async def handle_agent_error(self, agent_id: str, resume_reason: str = "error") -> bool:
        """Handle an agent error by attempting recovery.
        
        Args:
            agent_id: ID of the agent to recover
            resume_reason: Reason for resuming the agent
            
        Returns:
            bool: True if recovery successful
        """
        try:
            # Check cooldown
            if not self._can_restart(agent_id):
                logger.info(f"Agent {agent_id} in cooldown period")
                return False
                
            # Increment retry count
            retry_count = self._retry_counts.get(agent_id, 0) + 1
            self._retry_counts[agent_id] = retry_count
            
            if retry_count > self.max_retries:
                logger.error(f"Agent {agent_id} exceeded max retries")
                await self._log_failure(agent_id)
                return False
                
            # Attempt recovery
            logger.info(f"Attempting recovery for agent {agent_id} (attempt {retry_count})")
            
            # Stop agent
            await self.agent_ops.stop_agent(agent_id)
            
            # Wait for cooldown
            await asyncio.sleep(self.retry_cooldown)
            
            # Restart conversation
            if not await self._restart_conversation(agent_id, resume_reason):
                logger.error(f"Failed to restart conversation for agent {agent_id}")
                return False
                
            # Restart agent
            success = await self.agent_ops.start_agent(agent_id)
            
            if success:
                logger.info(f"Successfully recovered agent {agent_id}")
                self._last_restart[agent_id] = time.time()
                self._retry_counts[agent_id] = 0
                self.last_activity[agent_id] = time.time()
                return True
            else:
                logger.error(f"Failed to recover agent {agent_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling agent {agent_id} recovery: {e}")
            return False
            
    async def _monitor_heartbeats(self) -> None:
        """Monitor agent heartbeats and trigger recovery if needed."""
        try:
            while self._monitoring:
                for agent_id in await self.agent_ops.list_agents():
                    try:
                        # Check heartbeat
                        if await self._check_heartbeat(agent_id):
                            # Update activity timestamp
                            self.last_activity[agent_id] = time.time()
                            continue
                            
                        # Check if Cursor is idle
                        if await self._check_cursor_idle(agent_id):
                            logger.warning(f"Agent {agent_id} Cursor window idle")
                            await self.handle_agent_error(agent_id)
                            continue
                            
                        logger.warning(f"Agent {agent_id} heartbeat timeout")
                        await self.handle_agent_error(agent_id)
                        
                    except Exception as e:
                        logger.error(f"Error monitoring agent {agent_id}: {e}")
                        
                await asyncio.sleep(10)  # Check every 10 seconds
                
        except asyncio.CancelledError:
            logger.info("Heartbeat monitoring cancelled")
            raise
            
    async def start(self) -> bool:
        """Start the restarter.
        
        Returns:
            bool: True if start successful
        """
        if self._monitoring:
            return True
            
        try:
            self._monitoring = True
            self._monitor_task = asyncio.create_task(self._monitor_heartbeats())
            return True
            
        except Exception as e:
            logger.error(f"Failed to start agent restarter: {e}")
            self._monitoring = False
            return False
            
    async def stop(self) -> bool:
        """Stop the restarter.
        
        Returns:
            bool: True if stop successful
        """
        if not self._monitoring:
            return True
            
        try:
            self._monitoring = False
            if self._monitor_task:
                self._monitor_task.cancel()
                self._monitor_task = None
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop agent restarter: {e}")
            return False
            
    async def resume(self) -> bool:
        """Resume the restarter.
        
        Returns:
            bool: True if resume successful
        """
        return await self.start()
        
    async def _check_heartbeat(self, agent_id: str) -> bool:
        """Check if an agent's heartbeat is valid.
        
        Args:
            agent_id: ID of the agent to check
            
        Returns:
            bool: True if heartbeat is valid
        """
        try:
            status = await self.agent_status.get_agent_status(agent_id)
            if not status:
                return False
                
            last_heartbeat = status.get('last_heartbeat')
            if not last_heartbeat:
                return False
                
            # Check if heartbeat is within timeout
            heartbeat_time = datetime.fromisoformat(last_heartbeat)
            timeout = datetime.now() - timedelta(seconds=self.heartbeat_timeout)
            
            return heartbeat_time > timeout
            
        except Exception as e:
            logger.error(f"Error checking heartbeat for agent {agent_id}: {e}")
            return False
            
    def _can_restart(self, agent_id: str) -> bool:
        """Check if an agent can be restarted based on cooldown.
        
        Args:
            agent_id: ID of the agent to check
            
        Returns:
            bool: True if agent can be restarted
        """
        last_restart = self._last_restart.get(agent_id, 0)
        cooldown_elapsed = time.time() - last_restart >= self.restart_cooldown
        return cooldown_elapsed
        
    async def _log_failure(self, agent_id: str) -> None:
        """Log a permanent agent failure.
        
        Args:
            agent_id: ID of the failed agent
        """
        try:
            failure_log = {
                'agent_id': agent_id,
                'timestamp': datetime.now().isoformat(),
                'retry_count': self._retry_counts.get(agent_id, 0),
                'status': 'permanent_failure'
            }
            
            log_path = os.path.join('recovery', f'{agent_id}_failure.json')
            with open(log_path, 'w') as f:
                json.dump(failure_log, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error logging failure for agent {agent_id}: {e}") 