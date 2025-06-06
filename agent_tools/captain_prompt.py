"""
Captain Prompt System

Manages agent sequence and handles message/task integration for agent prompts.
"""

import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from messages.message_handler import MessageHandler
from messages.task_handler import TaskHandler

logger = logging.getLogger(__name__)

class CaptainPrompt:
    def __init__(self, base_dir: str = "messages"):
        """Initialize the captain prompt system.
        
        Args:
            base_dir: Base directory for message and task storage
        """
        self.message_handler = MessageHandler(base_dir)
        self.task_handler = TaskHandler(base_dir)
        self.sequence_file = os.path.join(base_dir, "sequence.json")
        self.wait_time = 300  # 5 minutes between prompts
        
    def _get_sequence_data(self) -> Dict:
        """Get current sequence data."""
        with open(self.sequence_file, 'r') as f:
            return json.load(f)
            
    def _format_waiting_messages(self, messages: List[Dict]) -> str:
        """Format waiting messages for display.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Formatted message string
        """
        if not messages:
            return "No messages waiting"
            
        formatted = "Waiting messages:\n"
        for msg in messages:
            from_agent = msg.get("from_agent", "Unknown")
            to_agent = msg.get("to_agent", "Unknown")
            timestamp = msg.get("timestamp", "Unknown")
            formatted += f"- From {from_agent} to {to_agent} at {timestamp}\n"
        return formatted.strip()
        
    def _get_agent_prompt(self, agent_id: str) -> str:
        """Generate prompt for an agent including messages and tasks.
        
        Args:
            agent_id: Agent ID to generate prompt for
            
        Returns:
            Formatted prompt string
        """
        # Get waiting messages
        messages = self.message_handler.get_messages(agent_id)
        message_count = len(messages)
        
        # Get current task
        task = self.task_handler.get_agent_task(agent_id)
        
        # Build prompt
        prompt = f"Agent-{agent_id}, you have {message_count} message(s) waiting for response.\n"
        
        if messages:
            prompt += "\n" + self._format_waiting_messages(messages) + "\n"
            
        if task:
            prompt += f"\nYour current task: {task}\n"
            
        prompt += "\nPlease respond in the message area."
        return prompt
        
    def run(self):
        """Run the captain prompt system."""
        logger.info("Starting Captain Prompt System")
        
        while True:
            try:
                # Get current sequence
                sequence_data = self._get_sequence_data()
                current_agent = sequence_data["last_agent"]
                next_agent = self.message_handler.get_next_agent()
                agent_order = sequence_data["agent_order"]
                
                # Get waiting messages
                messages = self.message_handler.get_messages(next_agent)
                message_count = len(messages)
                
                # Display status
                print("=" * 80)
                print(f"CAPTAIN PROMPT: {datetime.now().strftime('%H:%M:%S')}")
                print(f"Current agent in sequence: Agent-{current_agent}    ")
                print(f"Next agent: Agent-{next_agent}")
                print(f"Sequence: {'->'.join(agent_order)}")
                print(f"Messages waiting: {message_count}")
                
                if message_count > 0:
                    print("\n" + self._format_waiting_messages(messages))
                    
                print("=" * 80)
                
                # Generate and send prompt to next agent
                if next_agent:
                    prompt = self._get_agent_prompt(next_agent)
                    # TODO: Implement actual prompt sending mechanism
                    logger.info(f"Generated prompt for Agent-{next_agent}")
                    
                # Wait before next prompt
                logger.info(f"Waiting {self.wait_time} seconds before next prompt...")
                time.sleep(self.wait_time)
                
            except Exception as e:
                logger.error(f"Error in captain prompt system: {e}")
                time.sleep(60)  # Wait a minute before retrying
                
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    captain = CaptainPrompt()
    captain.run() 