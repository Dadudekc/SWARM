"""
System Orchestrator

Coordinates all Dream.OS components:
- Agent Management
- Task Management
- DevLog Management
- Cell Phone Communication
- Discord Integration
- System Logging
- Message History
- Captain Monitoring
"""

import logging
import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from ..messaging.cell_phone import CellPhone
from ..messaging.captain_phone import CaptainPhone
from .periodic_restart import AgentManager
from .task_manager import TaskManager, TaskStatus, TaskPriority
from .devlog_manager import DevLogManager
from ..messaging.unified_message_system import UnifiedMessageSystem
from social.utils.log_manager import LogManager, LogLevel

logger = logging.getLogger('dreamos.orchestrator')

class MessageRecord:
    """Record of a message between agents."""
    
    def __init__(
        self,
        sender_id: str,
        receiver_id: str,
        content: str,
        timestamp: datetime,
        message_id: Optional[str] = None
    ):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.timestamp = timestamp
        self.message_id = message_id or f"{timestamp.isoformat()}-{sender_id}-{receiver_id}"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageRecord':
        """Create from dictionary."""
        return cls(
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message_id=data["message_id"]
        )

class SystemOrchestrator:
    """Orchestrates all Dream.OS components."""
    
    def __init__(
        self,
        runtime_dir: Path,
        discord_token: str,
        channel_id: int,
        config_path: Optional[Path] = None
    ):
        """Initialize the system orchestrator.
        
        Args:
            runtime_dir: Base runtime directory
            discord_token: Discord bot token
            channel_id: Discord channel ID for devlogs
            config_path: Optional path to config file
        """
        self.runtime_dir = runtime_dir
        self.config_path = config_path or runtime_dir / "config" / "system_config.yaml"
        
        # Initialize logging
        self.log_manager = LogManager({
            'log_dir': str(runtime_dir / "logs"),
            'level': LogLevel.INFO,
            'platforms': {
                'system': 'system.log',
                'agents': 'agents.log',
                'tasks': 'tasks.log',
                'devlog': 'devlog.log',
                'messages': 'messages.log',
                'captain': 'captain.log'
            }
        })
        
        # Initialize components
        self.cell_phone = CellPhone()
        self.captain_phone = CaptainPhone()
        self.message_system = UnifiedMessageSystem(runtime_dir=runtime_dir)
        self.task_manager = TaskManager(runtime_dir=runtime_dir)
        self.devlog_manager = DevLogManager(
            discord_token=discord_token,
            channel_id=channel_id,
            runtime_dir=runtime_dir
        )
        self.agent_manager = AgentManager(
            runtime_dir=runtime_dir,
            discord_token=discord_token,
            channel_id=channel_id
        )
        
        # Message history storage
        self.message_history_file = runtime_dir / "data" / "message_history.json"
        self.message_history_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_message_history()
        
        # Captain monitoring
        self._monitor_task = None
        self._last_check = datetime.now(timezone.utc)
        self._response_timeout = timedelta(minutes=5)  # Time to wait for agent response
        
        # Connect components
        self._connect_components()
        
        # Log initialization
        self.log_manager.info(
            platform="system",
            status="success",
            message="System orchestrator initialized",
            tags=["startup", "init"]
        )
        
    def _load_message_history(self):
        """Load message history from file."""
        try:
            if self.message_history_file.exists():
                with open(self.message_history_file, 'r') as f:
                    data = json.load(f)
                    self.message_history = [
                        MessageRecord.from_dict(msg) for msg in data
                    ]
            else:
                self.message_history = []
                
            self.log_manager.info(
                platform="messages",
                status="success",
                message=f"Loaded {len(self.message_history)} message records",
                tags=["startup", "messages"]
            )
            
        except Exception as e:
            self.log_manager.error(
                platform="messages",
                status="error",
                message=f"Failed to load message history: {str(e)}",
                tags=["startup", "messages", "error"]
            )
            self.message_history = []
            
    def _save_message_history(self):
        """Save message history to file."""
        try:
            data = [msg.to_dict() for msg in self.message_history]
            with open(self.message_history_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.log_manager.info(
                platform="messages",
                status="success",
                message=f"Saved {len(self.message_history)} message records",
                tags=["shutdown", "messages"]
            )
            
        except Exception as e:
            self.log_manager.error(
                platform="messages",
                status="error",
                message=f"Failed to save message history: {str(e)}",
                tags=["shutdown", "messages", "error"]
            )
            
    async def record_message(
        self,
        sender_id: str,
        receiver_id: str,
        content: str,
        timestamp: Optional[datetime] = None
    ) -> MessageRecord:
        """Record a message between agents.
        
        Args:
            sender_id: ID of sending agent
            receiver_id: ID of receiving agent
            content: Message content
            timestamp: Optional timestamp (defaults to current time)
            
        Returns:
            MessageRecord: The recorded message
        """
        try:
            # Use current time if no timestamp provided
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
                
            # Create message record
            message = MessageRecord(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content,
                timestamp=timestamp
            )
            
            # Add to history
            self.message_history.append(message)
            
            # Save history
            self._save_message_history()
            
            # Log message
            self.log_manager.info(
                platform="messages",
                status="success",
                message=f"Recorded message from {sender_id} to {receiver_id}",
                tags=["message", "record"]
            )
            
            return message
            
        except Exception as e:
            self.log_manager.error(
                platform="messages",
                status="error",
                message=f"Failed to record message: {str(e)}",
                tags=["message", "record", "error"]
            )
            raise
            
    async def get_message_history(
        self,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[MessageRecord]:
        """Get message history with optional filtering.
        
        Args:
            agent_id: Filter by agent ID (either sender or receiver)
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of messages to return
            
        Returns:
            List[MessageRecord]: Filtered message history
        """
        try:
            # Filter messages
            filtered = self.message_history
            
            if agent_id:
                filtered = [
                    msg for msg in filtered
                    if msg.sender_id == agent_id or msg.receiver_id == agent_id
                ]
                
            if start_time:
                filtered = [
                    msg for msg in filtered
                    if msg.timestamp >= start_time
                ]
                
            if end_time:
                filtered = [
                    msg for msg in filtered
                    if msg.timestamp <= end_time
                ]
                
            # Sort by timestamp
            filtered.sort(key=lambda x: x.timestamp)
            
            # Apply limit
            if limit is not None:
                filtered = filtered[-limit:]
                
            # Log query
            self.log_manager.info(
                platform="messages",
                status="success",
                message=f"Retrieved {len(filtered)} messages",
                tags=["message", "query"]
            )
            
            return filtered
            
        except Exception as e:
            self.log_manager.error(
                platform="messages",
                status="error",
                message=f"Failed to get message history: {str(e)}",
                tags=["message", "query", "error"]
            )
            raise
            
    def _connect_components(self):
        """Connect all system components."""
        try:
            # Connect agent manager to cell phone
            self.agent_manager.cell_phone = self.cell_phone
            self.agent_manager.captain_phone = self.captain_phone
            
            # Connect task manager to devlog
            self.task_manager.devlog_manager = self.devlog_manager
            

            
            self.log_manager.info(
                platform="system",
                status="success",
                message="System components connected successfully",
                tags=["startup", "connect"]
            )
            
        except Exception as e:
            self.log_manager.error(
                platform="system",
                status="error",
                message=f"Failed to connect components: {str(e)}",
                tags=["startup", "connect"]
            )
            raise
        
    async def start(self):
        """Start all system components."""
        try:
            # Start Discord bot
            await self.devlog_manager.start()
            self.log_manager.info(
                platform="system",
                status="success",
                message="Discord bot started",
                tags=["startup", "discord"]
            )
            
            # Start agent management
            await self.agent_manager.start()
            self.log_manager.info(
                platform="system",
                status="success",
                message="Agent management started",
                tags=["startup", "agents"]
            )
            
            # Start captain monitoring
            self._monitor_task = asyncio.create_task(self._monitor_agents())
            self.log_manager.info(
                platform="captain",
                status="success",
                message="Captain monitoring started",
                tags=["startup", "captain"]
            )
            
            # Log system startup
            await self.devlog_manager.add_devlog_entry(
                agent_id="system",
                category="system",
                content="Dream.OS system started successfully"
            )
            
            self.log_manager.info(
                platform="system",
                status="success",
                message="System orchestrator started successfully",
                tags=["startup", "complete"]
            )
            
        except Exception as e:
            self.log_manager.error(
                platform="system",
                status="error",
                message=f"Failed to start system: {str(e)}",
                tags=["startup", "error"]
            )
            raise
            
    async def stop(self):
        """Stop all system components."""
        try:
            # Stop captain monitoring
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
                    
            self.log_manager.info(
                platform="captain",
                status="success",
                message="Captain monitoring stopped",
                tags=["shutdown", "captain"]
            )
            
            # Stop agent management
            await self.agent_manager.stop()
            self.log_manager.info(
                platform="system",
                status="success",
                message="Agent management stopped",
                tags=["shutdown", "agents"]
            )
            
            # Stop Discord bot
            await self.devlog_manager.stop()
            self.log_manager.info(
                platform="system",
                status="success",
                message="Discord bot stopped",
                tags=["shutdown", "discord"]
            )
            
            # Log system shutdown
            await self.devlog_manager.add_devlog_entry(
                agent_id="system",
                category="system",
                content="Dream.OS system shutting down"
            )
            
            self.log_manager.info(
                platform="system",
                status="success",
                message="System orchestrator stopped successfully",
                tags=["shutdown", "complete"]
            )
            
        except Exception as e:
            self.log_manager.error(
                platform="system",
                status="error",
                message=f"Error during system shutdown: {str(e)}",
                tags=["shutdown", "error"]
            )
            raise
            
    async def create_agent_task(
        self,
        agent_id: str,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: Optional[list[str]] = None
    ) -> str:
        """Create a new task for an agent."""
        try:
            task_id = await self.task_manager.create_task(
                title=title,
                description=description,
                assigned_agent=agent_id,
                priority=priority,
                dependencies=dependencies
            )
            
            # Log task creation
            self.log_manager.info(
                platform="tasks",
                status="success",
                message=f"Created task {task_id} for agent {agent_id}",
                tags=["task", "create"]
            )
            
            # Notify agent via cell phone
            await self.cell_phone.send_message(
                sender_id="system",
                receiver_id=agent_id,
                content=f"New task assigned: {title}\nPriority: {priority.value}\n\n{description}",
                mode="task"
            )
            
            return task_id
            
        except Exception as e:
            self.log_manager.error(
                platform="tasks",
                status="error",
                message=f"Failed to create task for agent {agent_id}: {str(e)}",
                tags=["task", "create", "error"]
            )
            raise
        
    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive status for an agent."""
        try:
            # Get task status
            tasks = await self.task_manager.get_agent_tasks(agent_id)
            task_summary = await self.task_manager.generate_task_summary(agent_id)
            
            # Get devlog entries
            devlog_entries = await self.devlog_manager.get_agent_entries(agent_id)
            
            # Get message history
            message_history = await self.cell_phone.get_message_history(agent_id)
            
            # Log status check
            self.log_manager.info(
                platform="agents",
                status="success",
                message=f"Retrieved status for agent {agent_id}",
                tags=["status", "check"]
            )
            
            return {
                "agent_id": agent_id,
                "tasks": {
                    "total": len(tasks),
                    "summary": task_summary,
                    "recent": tasks[:5]  # Last 5 tasks
                },
                "devlog": {
                    "total_entries": len(devlog_entries),
                    "recent_entries": devlog_entries[:5]  # Last 5 entries
                },
                "messages": {
                    "total": len(message_history),
                    "recent": message_history[:5]  # Last 5 messages
                }
            }
            
        except Exception as e:
            self.log_manager.error(
                platform="agents",
                status="error",
                message=f"Failed to get status for agent {agent_id}: {str(e)}",
                tags=["status", "check", "error"]
            )
            raise
            
    async def close(self):
        """Clean up resources."""
        try:
            # Save message history
            self._save_message_history()
            
            # Log shutdown
            self.log_manager.info(
                platform="system",
                status="success",
                message="System orchestrator shut down successfully",
                tags=["shutdown", "complete"]
            )
            
        except Exception as e:
            self.log_manager.error(
                platform="system",
                status="error",
                message=f"Error during shutdown: {str(e)}",
                tags=["shutdown", "error"]
            )
            raise
            
    async def _monitor_agents(self):
        """Monitor agent communications and respond as Captain."""
        try:
            while True:
                # Check for new messages
                current_time = datetime.now(timezone.utc)
                recent_messages = await self.get_message_history(
                    start_time=self._last_check
                )
                
                for message in recent_messages:
                    # Skip system messages
                    if message.sender_id == "system":
                        continue
                        
                    # Check if message needs response
                    if self._needs_captain_response(message):
                        await self._handle_agent_message(message)
                        
                # Update last check time
                self._last_check = current_time
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.log_manager.error(
                platform="captain",
                status="error",
                message=f"Error in agent monitoring: {str(e)}",
                tags=["monitor", "error"]
            )
            # Restart monitoring
            self._monitor_task = asyncio.create_task(self._monitor_agents())
            
    def _needs_captain_response(self, message: MessageRecord) -> bool:
        """Check if a message needs Captain's response."""
        # Check if message is recent enough
        if datetime.now(timezone.utc) - message.timestamp > self._response_timeout:
            return False
            
        # Check message content for keywords
        content = message.content.lower()
        keywords = [
            "help", "assist", "support", "question", "issue",
            "problem", "error", "failed", "stuck", "confused"
        ]
        
        return any(keyword in content for keyword in keywords)
        
    async def _handle_agent_message(self, message: MessageRecord):
        """Handle an agent message that needs Captain's response."""
        try:
            # Log the message
            self.log_manager.info(
                platform="captain",
                status="success",
                message=f"Processing message from {message.sender_id}",
                tags=["captain", "message"]
            )
            
            # Generate response based on message content
            response = await self._generate_captain_response(message)
            
            # Send response
            await self.captain_phone.send_message(
                sender_id="captain",
                receiver_id=message.sender_id,
                content=response,
                mode="response"
            )
            
            # Record the response
            await self.record_message(
                sender_id="captain",
                receiver_id=message.sender_id,
                content=response,
                timestamp=datetime.now(timezone.utc)
            )
            
            self.log_manager.info(
                platform="captain",
                status="success",
                message=f"Sent response to {message.sender_id}",
                tags=["captain", "response"]
            )
            
        except Exception as e:
            self.log_manager.error(
                platform="captain",
                status="error",
                message=f"Error handling agent message: {str(e)}",
                tags=["captain", "error"]
            )
            
    async def _generate_captain_response(self, message: MessageRecord) -> str:
        """Generate a Captain's response to an agent message."""
        # Get agent status
        status = await self.get_agent_status(message.sender_id)
        
        # Get recent tasks
        tasks = status["tasks"]["recent"]
        
        # Generate response
        response = f"Hello {message.sender_id},\n\n"
        
        if tasks:
            response += "I see you're working on these tasks:\n"
            for task in tasks:
                response += f"- {task['title']} ({task['status']})\n"
            response += "\n"
            
        response += "How can I help you with your current task? I'm here to provide guidance and support.\n\n"
        response += "Best regards,\nCaptain"
        
        return response 