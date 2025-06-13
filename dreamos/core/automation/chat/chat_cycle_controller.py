"""
Chat Cycle Controller

Orchestrates the scraping process and manages chat cycles.
"""

import logging
import time
import asyncio
from typing import Optional, Dict, List, Any
from pathlib import Path
import json

from .chat_scraper_service import ChatScraperService
from .chat_manager import ChatManager
from .prompt_engine import PromptEngine
from ..config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class ChatCycleController:
    """Orchestrates the scraping process and manages chat cycles."""
    
    def __init__(self, config_path: str):
        """Initialize chat cycle controller.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_bridge_config()
        
        # Initialize components
        self.scraper = ChatScraperService(config_path)
        self.chat_manager = ChatManager(config_path)
        self.prompt_engine = PromptEngine(config_path)
        
        # Load cycle configuration
        self.cycle_config = self._load_cycle_config()
        
        # State tracking
        self.is_running = False
        self.current_cycle = 0
        self.cycle_start_time = None
        self.last_cycle_time = None
        
    def _load_cycle_config(self) -> Dict[str, Any]:
        """Load cycle configuration.
        
        Returns:
            Cycle configuration
        """
        config_path = Path("config/cycle_config.json")
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
                
        # Default configuration
        return {
            "max_cycles": 100,
            "cycle_interval": 300,  # 5 minutes
            "max_retries": 3,
            "retry_delay": 60,  # 1 minute
            "timeout": 3600,  # 1 hour
            "memory_limit": 1000,  # messages
            "rate_limit": {
                "requests_per_minute": 20,
                "burst_limit": 5
            }
        }
        
    async def start(self):
        """Start the chat cycle controller."""
        if self.is_running:
            logger.warning("Controller already running")
            return
            
        try:
            # Start components
            self.scraper.start()
            self.chat_manager.start()
            self.prompt_engine.start()
            
            self.is_running = True
            self.cycle_start_time = time.time()
            logger.info("Chat cycle controller started")
            
            # Start cycle loop
            await self._run_cycle_loop()
            
        except Exception as e:
            logger.error(f"Error starting controller: {e}")
            await self.stop()
            
    async def stop(self):
        """Stop the chat cycle controller."""
        if not self.is_running:
            return
            
        try:
            # Stop components
            self.scraper.stop()
            self.chat_manager.stop()
            self.prompt_engine.stop()
            
            self.is_running = False
            logger.info("Chat cycle controller stopped")
            
        except Exception as e:
            logger.error(f"Error stopping controller: {e}")
            
    async def _run_cycle_loop(self):
        """Run the main cycle loop."""
        while self.is_running:
            try:
                # Check cycle limits
                if self._should_stop_cycle():
                    logger.info("Cycle limit reached, stopping")
                    await self.stop()
                    break
                    
                # Run cycle
                await self._run_single_cycle()
                
                # Update cycle state
                self.current_cycle += 1
                self.last_cycle_time = time.time()
                
                # Wait for next cycle
                await asyncio.sleep(self.cycle_config["cycle_interval"])
                
            except Exception as e:
                logger.error(f"Error in cycle loop: {e}")
                await asyncio.sleep(self.cycle_config["retry_delay"])
                
    def _should_stop_cycle(self) -> bool:
        """Check if cycle should stop.
        
        Returns:
            Whether cycle should stop
        """
        # Check cycle count
        if self.current_cycle >= self.cycle_config["max_cycles"]:
            return True
            
        # Check timeout
        if time.time() - self.cycle_start_time > self.cycle_config["timeout"]:
            return True
            
        # Check memory limit
        if len(self.chat_manager.get_chat_history()) > self.cycle_config["memory_limit"]:
            return True
            
        return False
        
    async def _run_single_cycle(self):
        """Run a single chat cycle."""
        try:
            # Verify login
            if not self.chat_manager.verify_login():
                logger.error("Login verification failed")
                return
                
            # Get chat titles
            chat_titles = self.chat_manager.get_chat_titles()
            if not chat_titles:
                logger.warning("No chat titles found")
                return
                
            # Process each chat
            for title in chat_titles:
                if not self.is_running:
                    break
                    
                await self._process_chat(title)
                
        except Exception as e:
            logger.error(f"Error in chat cycle: {e}")
            
    async def _process_chat(self, title: str):
        """Process a single chat.
        
        Args:
            title: Chat title
        """
        try:
            # Get chat history
            history = self.chat_manager.get_chat_history(title)
            
            # Generate prompt based on history
            prompt = self._generate_prompt(title, history)
            
            # Execute prompt
            response = await self.chat_manager.execute_prompt(title, prompt)
            
            if response:
                logger.info(f"Got response for chat: {title}")
                
        except Exception as e:
            logger.error(f"Error processing chat {title}: {e}")
            
    def _generate_prompt(self, title: str, history: List[Dict[str, str]]) -> str:
        """Generate prompt based on chat history.
        
        Args:
            title: Chat title
            history: Chat history
            
        Returns:
            Generated prompt
        """
        # TODO: Implement prompt generation logic
        return f"Continue the conversation about {title}"
        
    def get_status(self) -> Dict[str, Any]:
        """Get controller status.
        
        Returns:
            Status information
        """
        return {
            "is_running": self.is_running,
            "current_cycle": self.current_cycle,
            "cycle_start_time": self.cycle_start_time,
            "last_cycle_time": self.last_cycle_time,
            "memory_usage": len(self.chat_manager.get_chat_history()),
            "active_chats": len(self.chat_manager.get_chat_titles())
        }
        
    def cleanup(self):
        """Clean up resources."""
        try:
            self.scraper.cleanup()
            self.chat_manager.cleanup()
            self.prompt_engine.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}") 