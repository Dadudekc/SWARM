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
from .chatgpt_bridge import ChatGPTBridge

class LLMAgent:
    """Agent that integrates ChatGPT with the messaging system."""
    
    def __init__(
        self,
        agent_id: str,
        message_system: UnifiedMessageSystem,
        chatgpt_bridge: ChatGPTBridge,
        system_prompt: Optional[str] = None
    ):
        self.agent_id = agent_id
        self.message_system = message_system
        self.chatgpt_bridge = chatgpt_bridge
        self.conversation_history = []
        self.system_prompt = system_prompt or "You are a helpful AI assistant."
        asyncio.create_task(self._setup_subscriptions())
    
    async def _setup_subscriptions(self):
        """Set up message subscriptions."""
        await self.message_system.subscribe(
            self.agent_id,
            self._handle_message
        )
        await self.message_system.subscribe_pattern(
            f"{self.agent_id}.*",
            self._handle_message
        )
    
    async def _handle_message(self, message: Message) -> None:
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
            
            # Send response back through messaging system
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
            # Send error response
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
        # Unsubscribe from messages
        await self.message_system.unsubscribe(self.agent_id, self._handle_message)
        await self.message_system.unsubscribe_pattern(f"{self.agent_id}.*", self._handle_message)
        
        # Clear history
        await self.clear_history()
    
    async def cleanup(self) -> None:
        await self.shutdown() 