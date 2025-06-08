"""
LLM Agent Integration
-------------------
Provides integration between ChatGPT and the messaging system.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..messaging.unified_message_system import UnifiedMessageSystem
from ..messaging.common import Message, MessageMode, MessagePriority
from ..bridge.chatgpt.bridge import ChatGPTBridge

class LLMAgent:
    """Agent that integrates ChatGPT with the messaging system."""
    
    def __init__(
        self,
        agent_id: str,
        message_system: Optional[UnifiedMessageSystem],
        chatgpt_bridge: ChatGPTBridge,
        system_prompt: Optional[str] = None
    ):
        """Initialize the LLM agent.
        
        Args:
            agent_id: Unique identifier for this agent
            message_system: Optional message system for communication
            chatgpt_bridge: Bridge to ChatGPT API
            system_prompt: Optional system prompt for ChatGPT
        """
        self.agent_id = agent_id
        self.message_system = message_system
        self.chatgpt_bridge = chatgpt_bridge
        self.conversation_history = []
        self.system_prompt = system_prompt or "You are a helpful AI assistant."
        self._subscription_task = None
    
    async def initialize(self):
        """Initialize the agent and set up subscriptions."""
        if self.message_system is not None:
            self._subscription_task = asyncio.create_task(self._setup_subscriptions())
            try:
                await self._subscription_task
            except Exception as e:
                self.logger.error(
                    platform="llm_agent",
                    status="error",
                    message=f"Failed to set up subscriptions: {str(e)}",
                    tags=["init", "error"]
                )
                raise
    
    async def _setup_subscriptions(self):
        """Set up message subscriptions."""
        if self.message_system is None:
            self.logger.warning(
                platform="llm_agent",
                status="warning",
                message="No message system available - skipping subscriptions",
                tags=["init", "warning"]
            )
            return
            
        try:
            await self.message_system.subscribe(
                topic=f"agent.{self.agent_id}.commands",
                handler=self._handle_command
            )
            self.logger.info(
                platform="llm_agent",
                status="success",
                message=f"Successfully subscribed to commands for {self.agent_id}",
                tags=["init", "success"]
            )
        except Exception as e:
            self.logger.error(
                platform="llm_agent",
                status="error",
                message=f"Error setting up subscriptions: {str(e)}",
                tags=["init", "error"]
            )
            raise
    
    async def _handle_command(self, message: Message):
        """Handle incoming messages."""
        try:
            # Add user message to conversation history
            self.conversation_history.append(
                self.chatgpt_bridge.format_user_message(message.content)
            )
            
            # Prepare messages for ChatGPT
            messages = [self.chatgpt_bridge.format_system_message(self.system_prompt)]
            messages.extend(self.conversation_history)
            
            # Get response from ChatGPT
            response = await self.chatgpt_bridge.chat(messages)
            
            # Extract response content
            response_content = response["choices"][0]["message"]["content"]
            
            # Add assistant response to conversation history
            self.conversation_history.append(
                self.chatgpt_bridge.format_assistant_message(response_content)
            )
            
            # Send response back through messaging system if available
            if self.message_system is not None:
                response_message = Message(
                    from_agent=self.agent_id,
                    to_agent=message.from_agent,
                    content=response_content,
                    mode=MessageMode.NORMAL,
                    priority=MessagePriority.NORMAL.value,
                    metadata={
                        "original_message_id": getattr(message, 'message_id', None),
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                await self.message_system.send_message(response_message)
            
        except Exception as e:
            # Send error response if messaging system is available
            if self.message_system is not None:
                error_message = Message(
                    from_agent=self.agent_id,
                    to_agent=message.from_agent,
                    content=f"Error processing message: {str(e)}",
                    mode=MessageMode.NORMAL,
                    priority=MessagePriority.HIGH.value,
                    metadata={
                        "original_message_id": getattr(message, 'message_id', None),
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                await self.message_system.send_message(error_message)
    
    async def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
    
    async def update_system_prompt(self, new_prompt: str) -> None:
        """Update the system prompt."""
        self.system_prompt = new_prompt
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self.conversation_history
    
    async def shutdown(self) -> None:
        """Clean up resources."""
        if self._subscription_task:
            self._subscription_task.cancel()
            try:
                await self._subscription_task
            except asyncio.CancelledError:
                pass
                
        if self.message_system is not None:
            # Unsubscribe from messages
            await self.message_system.unsubscribe(self.agent_id, self._handle_command)
            await self.message_system.unsubscribe_pattern(f"{self.agent_id}.*", self._handle_command)
        
        # Clear history
        await self.clear_history()
    
    async def cleanup(self) -> None:
        await self.shutdown() 
