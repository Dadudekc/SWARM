"""
Chat Manager

Handles high-level chat operations and memory management.
"""

import logging
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .chat_scraper_service import ChatScraperService
from ..config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class ChatManager:
    """Manages ChatGPT conversations and memory."""
    
    def __init__(self, config_path: str):
        """Initialize chat manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_bridge_config()
        
        self.scraper = ChatScraperService(config_path)
        self.memory_file = Path("data/chat_memory.json")
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.memory: Dict[str, Any] = self._load_memory()
        
    def _load_memory(self) -> Dict[str, Any]:
        """Load chat memory from file.
        
        Returns:
            Memory data
        """
        if self.memory_file.exists():
            try:
                return json.loads(self.memory_file.read_text())
            except Exception as e:
                logger.error(f"Error loading memory: {e}")
        return {
            "chats": {},
            "last_update": datetime.now().isoformat()
        }
        
    def _save_memory(self):
        """Save chat memory to file."""
        try:
            self.memory["last_update"] = datetime.now().isoformat()
            self.memory_file.write_text(json.dumps(self.memory, indent=2))
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
            
    def start(self):
        """Start the chat manager."""
        self.scraper.start()
        logger.info("Chat manager started")
        
    def stop(self):
        """Stop the chat manager."""
        self.scraper.stop()
        self._save_memory()
        logger.info("Chat manager stopped")
        
    def verify_login(self) -> bool:
        """Verify ChatGPT login status.
        
        Returns:
            Whether login is valid
        """
        return self.scraper.validate_login()
        
    def get_chat_titles(self) -> List[str]:
        """Get all chat titles.
        
        Returns:
            List of chat titles
        """
        chats = self.scraper.get_all_chats()
        return [chat["title"] for chat in chats]
        
    def execute_prompt(self, prompt: str, chat_title: Optional[str] = None) -> Optional[str]:
        """Execute prompt in specified or current chat.
        
        Args:
            prompt: Prompt to execute
            chat_title: Optional chat title to use
            
        Returns:
            Response text or None
        """
        try:
            # Navigate to chat if specified
            if chat_title:
                chats = self.scraper.get_all_chats()
                chat = next((c for c in chats if c["title"] == chat_title), None)
                if not chat:
                    logger.error(f"Chat not found: {chat_title}")
                    return None
                    
                self.scraper.browser.navigate_to(chat["link"])
                time.sleep(2)  # Wait for chat to load
                
            # Send prompt
            response = self.scraper.send_prompt(prompt)
            
            # Update memory
            if response:
                self._update_memory(chat_title or "current", prompt, response)
                
            return response
            
        except Exception as e:
            logger.error(f"Error executing prompt: {e}")
            return None
            
    def _update_memory(self, chat_title: str, prompt: str, response: str):
        """Update chat memory.
        
        Args:
            chat_title: Title of chat
            prompt: Prompt sent
            response: Response received
        """
        if chat_title not in self.memory["chats"]:
            self.memory["chats"][chat_title] = []
            
        self.memory["chats"][chat_title].append({
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response
        })
        
        self._save_memory()
        
    def get_chat_history(self, chat_title: str) -> List[Dict[str, str]]:
        """Get chat history.
        
        Args:
            chat_title: Title of chat
            
        Returns:
            List of chat interactions
        """
        return self.memory["chats"].get(chat_title, [])
        
    def clear_chat_history(self, chat_title: str):
        """Clear chat history.
        
        Args:
            chat_title: Title of chat
        """
        if chat_title in self.memory["chats"]:
            del self.memory["chats"][chat_title]
            self._save_memory()
            
    def cleanup(self):
        """Clean up resources."""
        try:
            self.scraper.cleanup()
            self._save_memory()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}") 