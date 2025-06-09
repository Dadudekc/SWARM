"""
Agent Onboarder Module

Handles initial agent activation and setup, including role-specific welcome messages
and UI interaction for new agent instances.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

import pyautogui
import win32gui
import win32con
import win32process
import psutil

from dreamos.core.agent_control.agent_operations import AgentOperations
from dreamos.core.agent_control.agent_status import AgentStatus
from dreamos.core.agent_control.agent_cellphone import AgentCellphone

logger = logging.getLogger(__name__)

class AgentOnboarder:
    """Handles initial agent activation and setup."""
    
    def __init__(self,
                 agent_ops: AgentOperations,
                 agent_status: AgentStatus,
                 cellphone: Optional[AgentCellphone] = None,
                 config: Optional[Dict] = None):
        """Initialize the agent onboarder.
        
        Args:
            agent_ops: Agent operations interface
            agent_status: Agent status tracker
            cellphone: Optional agent cellphone instance for message injection
            config: Optional configuration dictionary
        """
        self.agent_ops = agent_ops
        self.agent_status = agent_status
        self.cellphone = cellphone or AgentCellphone(config)
        self.config = config or {}
        
        # Test mode configuration
        self.test_mode = os.environ.get("DREAMOS_TEST_MODE") == "1"
        if self.test_mode:
            logger.info("AgentOnboarder running in test mode - UI interactions disabled")
        
        # Timing configuration (reuse from restarter)
        self.timing = {
            'delay_after_ctrl_n': self.config.get('delay_after_ctrl_n', 0.5),
            'delay_after_click': self.config.get('delay_after_click', 0.3),
            'delay_between_keys': self.config.get('delay_between_keys', 0.02),
            'delay_after_window_activate': self.config.get('delay_after_window_activate', 0.5),
            'delay_between_agents': self.config.get('delay_between_agents', 2.0)  # Stagger agent starts
        }
        
        # Coordinate management
        self.coords_file = Path('config/cursor_agent_coords.json')
        self.input_coords: Dict[str, Tuple[int, int]] = {}
        
        # Role configurations
        self.roles_dir = Path('config/agent_roles')
        self.role_configs: Dict[str, Dict] = {}
        
        # State tracking
        self._initialized = False
        self._onboarding_agents: Set[str] = set()
        
    async def initialize(self) -> bool:
        """Initialize the onboarder.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Load coordinates
            await self._load_coordinates()
            
            # Load role configurations
            await self._load_role_configs()
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize agent onboarder: {e}")
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
            
    async def _load_role_configs(self) -> None:
        """Load role configurations from files."""
        try:
            if not self.roles_dir.exists():
                logger.warning(f"Roles directory not found: {self.roles_dir}")
                return
                
            for role_file in self.roles_dir.glob('*.json'):
                try:
                    with open(role_file, 'r') as f:
                        role_config = json.load(f)
                        role_name = role_file.stem
                        self.role_configs[role_name] = role_config
                except Exception as e:
                    logger.error(f"Error loading role config {role_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error loading role configurations: {e}")
            
    async def _get_role_welcome(self, agent_id: str, role: str) -> str:
        """Get welcome message for an agent's role.
        
        Args:
            agent_id: ID of the agent
            role: Role of the agent
            
        Returns:
            str: Welcome message
        """
        try:
            # Get role config
            role_config = self.role_configs.get(role, {})
            welcome_template = role_config.get('welcome_message', 
                "Hello, I am {agent_id}, your {role} assistant. How can I help you today?")
                
            # Apply substitutions
            welcome = welcome_template.format(
                agent_id=agent_id,
                role=role,
                timestamp=datetime.now().isoformat()
            )
            
            return welcome
            
        except Exception as e:
            logger.error(f"Error getting welcome message for agent {agent_id}: {e}")
            return f"Hello, I am {agent_id}. How can I help you today?"
            
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
                if class_name == "Chrome_WidgetWin_1":  # Cursor's window class
                    title = win32gui.GetWindowText(hwnd)
                    if agent_id in title:
                        windows.append(hwnd)
            return True
            
        windows = []
        win32gui.EnumWindows(callback, windows)
        return windows[0] if windows else None
        
    async def _start_new_conversation(self, agent_id: str, role: str) -> bool:
        """Start a new conversation for an agent.
        
        Args:
            agent_id: ID of the agent
            role: Role of the agent
            
        Returns:
            bool: True if conversation started successfully
        """
        if self.test_mode:
            logger.info(f"[TEST MODE] Skipping UI interaction for agent {agent_id}")
            return True
            
        try:
            # Get welcome message
            welcome = await self._get_role_welcome(agent_id, role)
            
            # Inject welcome message using cellphone
            if not await self.cellphone.inject_prompt(agent_id, welcome):
                logger.error(f"Failed to inject welcome message for agent {agent_id}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error starting conversation for agent {agent_id}: {e}")
            return False
            
    async def onboard_agent(self, agent_id: str, role: str) -> bool:
        """Onboard a new agent.
        
        Args:
            agent_id: ID of the agent to onboard
            role: Role of the agent
            
        Returns:
            bool: True if onboarding successful
        """
        if not self._initialized:
            logger.error("Onboarder not initialized")
            return False
            
        if agent_id in self._onboarding_agents:
            logger.warning(f"Agent {agent_id} already being onboarded")
            return False
            
        try:
            self._onboarding_agents.add(agent_id)
            
            # Start agent
            if not await self.agent_ops.start_agent(agent_id):
                logger.error(f"Failed to start agent {agent_id}")
                return False
                
            # Wait for agent to be ready
            await asyncio.sleep(self.timing['delay_between_agents'])
            
            # Start conversation
            if not await self._start_new_conversation(agent_id, role):
                logger.error(f"Failed to start conversation for agent {agent_id}")
                return False
                
            # Update status
            await self.agent_status.update_agent_status(agent_id, {
                'status': 'active',
                'role': role,
                'onboarded_at': datetime.now().isoformat()
            })
            
            logger.info(f"Successfully onboarded agent {agent_id} as {role}")
            return True
            
        except Exception as e:
            logger.error(f"Error onboarding agent {agent_id}: {e}")
            return False
            
        finally:
            self._onboarding_agents.discard(agent_id)
            
    async def onboard_agents(self, agent_roles: Dict[str, str]) -> bool:
        """Onboard multiple agents.
        
        Args:
            agent_roles: Dictionary mapping agent IDs to roles
            
        Returns:
            bool: True if all agents onboarded successfully
        """
        try:
            for agent_id, role in agent_roles.items():
                if not await self.onboard_agent(agent_id, role):
                    logger.error(f"Failed to onboard agent {agent_id}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error onboarding agents: {e}")
            return False

    async def start(self) -> bool:
        """No-op for controller lifecycle compatibility."""
        return True

    async def stop(self) -> bool:
        """No-op for controller lifecycle compatibility."""
        return True

    async def resume(self) -> bool:
        """No-op for controller lifecycle compatibility."""
        return True 