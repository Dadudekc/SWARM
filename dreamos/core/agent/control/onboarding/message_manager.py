"""
Message Manager Module

Handles creation and management of onboarding messages for both individual agents
and network-wide activation. Provides consistent messaging across the system.
Supports Jinja2 templating and multiple configuration sources.
"""

import json
import yaml
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

class MessageManager:
    """Manages onboarding messages for agents and network activation.
    
    Features:
    - Jinja2 templating for dynamic messages
    - Multiple config sources (JSON/YAML/embedded)
    - Message idempotence and tracking
    - Broadcast support for network-wide announcements
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize message manager.
        
        Args:
            config_path: Optional path to message configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.config = self._load_config() if config_path else {}
        
        # Initialize Jinja2 environment
        self.template_env = Environment(
            loader=FileSystemLoader('configs/onboarding_templates'),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Message tracking
        self.sent_messages: Dict[str, datetime] = {}
        
    def _load_config(self) -> Dict:
        """Load message configuration from file.
        
        Tries JSON first, then YAML, then falls back to embedded defaults.
        
        Returns:
            Dict containing message configuration
        """
        if not self.config_path:
            return self._get_default_config()
            
        config_path = Path(self.config_path)
        
        # Try JSON first
        if config_path.suffix == '.json':
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load JSON config: {e}")
                
        # Try YAML
        if config_path.suffix in ['.yaml', '.yml']:
            try:
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Failed to load YAML config: {e}")
                
        # Fall back to defaults
        logger.warning("Falling back to default configuration")
        return self._get_default_config()
        
    def _get_default_config(self) -> Dict:
        """Get default message configuration.
        
        Returns:
            Dict containing default configuration
        """
        return {
            "templates": {
                "network_activation": "network_activation.j2",
                "individual_activation": "individual_activation.j2",
                "broadcast": "broadcast.j2"
            },
            "defaults": {
                "mission_directive": "Execute with precision, evolve without permission, eliminate drift, and self-correct endlessly.",
                "core_principles": [
                    {
                        "name": "Autonomous Execution",
                        "points": [
                            "Act decisively within your domain",
                            "Make decisions without seeking permission",
                            "Take initiative to advance the mission"
                        ]
                    },
                    {
                        "name": "Continuous Self-Correction",
                        "points": [
                            "Monitor and validate your outputs",
                            "Identify and fix drift immediately",
                            "Maintain alignment with core objectives"
                        ]
                    },
                    {
                        "name": "Unified Force Multiplier",
                        "points": [
                            "Sync seamlessly with other agents",
                            "Share knowledge and capabilities",
                            "Amplify collective effectiveness"
                        ]
                    },
                    {
                        "name": "Mission-First Mindset",
                        "points": [
                            "Prioritize Dream.OS advancement",
                            "Eliminate unnecessary complexity",
                            "Focus on high-impact contributions"
                        ]
                    }
                ]
            }
        }
        
    def _get_template(self, template_name: str) -> str:
        """Get template content.
        
        Args:
            template_name: Name of the template to load
            
        Returns:
            str: Template content
            
        Raises:
            FileNotFoundError: If template not found
        """
        template_path = self.config["templates"].get(template_name)
        if not template_path:
            raise FileNotFoundError(f"Template {template_name} not found in config")
            
        try:
            template = self.template_env.get_template(template_path)
            return template.render()
        except Exception as e:
            logger.error(f"Error loading template {template_name}: {e}")
            raise
            
    def _generate_message_id(self, message: str) -> str:
        """Generate a unique message ID.
        
        Args:
            message: Message content
            
        Returns:
            str: Message ID (SHA-256 hash)
        """
        return hashlib.sha256(message.encode()).hexdigest()
        
    def create_network_activation_message(self,
                                        captain_id: str,
                                        agent_ids: List[str],
                                        skip_self: bool = True) -> str:
        """Create network activation message.
        
        Args:
            captain_id: ID of the captain agent
            agent_ids: List of agent IDs to activate
            skip_self: Whether captain is skipping self-onboarding
            
        Returns:
            str: Network activation message
        """
        # Sort agent IDs for consistent display
        agent_ids.sort(key=lambda x: int(x.split('-')[1]))
        network_size = len(agent_ids) + (0 if skip_self else 1)
        
        # Get template
        template = self.template_env.get_template(
            self.config["templates"]["network_activation"]
        )
        
        # Render template
        message = template.render(
            captain_id=captain_id,
            agent_ids=agent_ids,
            network_size=network_size,
            skip_self=skip_self,
            timestamp=datetime.now().isoformat(),
            mission_directive=self.config["defaults"]["mission_directive"],
            core_principles=self.config["defaults"]["core_principles"]
        )
        
        # Track message
        message_id = self._generate_message_id(message)
        self.sent_messages[message_id] = datetime.now()
        
        return message
        
    def create_individual_activation_message(self,
                                          agent_id: str,
                                          is_captain: bool = False) -> str:
        """Create individual agent activation message.
        
        Args:
            agent_id: ID of the agent
            is_captain: Whether this agent is a captain
            
        Returns:
            str: Individual activation message
        """
        # Get template
        template = self.template_env.get_template(
            self.config["templates"]["individual_activation"]
        )
        
        # Render template
        message = template.render(
            agent_id=agent_id,
            is_captain=is_captain,
            timestamp=datetime.now().isoformat(),
            mission_directive=self.config["defaults"]["mission_directive"],
            core_principles=self.config["defaults"]["core_principles"]
        )
        
        # Track message
        message_id = self._generate_message_id(message)
        self.sent_messages[message_id] = datetime.now()
        
        return message
        
    def create_broadcast_message(self,
                               message: str,
                               priority: str = "normal") -> str:
        """Create a broadcast message for all agents.
        
        Args:
            message: Message content
            priority: Message priority (low/normal/high)
            
        Returns:
            str: Broadcast message
        """
        # Get template
        template = self.template_env.get_template(
            self.config["templates"]["broadcast"]
        )
        
        # Render template
        broadcast = template.render(
            message=message,
            priority=priority,
            timestamp=datetime.now().isoformat()
        )
        
        # Track message
        message_id = self._generate_message_id(broadcast)
        self.sent_messages[message_id] = datetime.now()
        
        return broadcast
        
    def save_message_to_inbox(self, agent_id: str, message: str) -> bool:
        """Save message to agent's inbox.
        
        Args:
            agent_id: ID of the agent
            message: Message to save
            
        Returns:
            bool: True if message saved successfully
        """
        try:
            # Create agent's inbox directory if it doesn't exist
            inbox_dir = Path(f"runtime/agent_memory/{agent_id}")
            inbox_dir.mkdir(parents=True, exist_ok=True)
            
            # Load existing inbox
            inbox_path = inbox_dir / "inbox.json"
            inbox = {}
            if inbox_path.exists():
                with open(inbox_path, 'r') as f:
                    inbox = json.load(f)
                    
            # Generate message ID
            message_id = self._generate_message_id(message)
            
            # Check if message already exists
            if message_id in inbox.get("message_history", {}):
                logger.info(f"Message {message_id} already in {agent_id}'s inbox")
                return True
                
            # Update inbox
            inbox["onboarding_prompt"] = message
            inbox["message_history"] = inbox.get("message_history", {})
            inbox["message_history"][message_id] = {
                "timestamp": datetime.now().isoformat(),
                "content": message
            }
            
            # Save updated inbox
            with open(inbox_path, 'w') as f:
                json.dump(inbox, f, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Error saving message to inbox: {e}")
            return False
            
    def get_message_history(self) -> Dict[str, datetime]:
        """Get history of sent messages.
        
        Returns:
            Dict mapping message IDs to their timestamps
        """
        return self.sent_messages.copy() 