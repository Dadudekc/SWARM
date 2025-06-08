"""
Enhanced Response Loop Daemon
---------------------------
Enhanced implementation of the response loop daemon with hybrid completion detection.
"""

import asyncio
import json
import logging
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pyautogui
import cv2
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .base.response_loop_daemon import BaseResponseLoopDaemon, ResponseProcessor
from .handlers.bridge_outbox_handler import BridgeOutboxHandler
from .validation.engine import ValidationEngine
from .memory.response_memory_tracker import ResponseMemoryTracker
from .processors.factory import ResponseProcessorFactory
from .processors.mode import ProcessorMode
from ..agent_control.response_capture import ResponseCapture
from ..agent_control.ui_automation import UIAutomation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedResponseLoopDaemon(BaseResponseLoopDaemon):
    """Enhanced response loop daemon with hybrid completion detection."""
    
    def __init__(self, config_path: str, discord_token: Optional[str] = None):
        """Initialize the enhanced response loop daemon.
        
        Args:
            config_path: Path to configuration file
            discord_token: Optional Discord token for notifications
        """
        super().__init__(config_path, discord_token)
        
        # Initialize validation engine
        self.validation_engine = ValidationEngine()
        
        # Initialize memory tracker
        memory_path = Path(self.config["paths"]["runtime"]) / "memory" / f"response_log_{self.agent_id}.json"
        self.memory_tracker = ResponseMemoryTracker(str(memory_path))
        
        # Initialize UI automation and response capture
        self.ui_automation = UIAutomation(config_path)
        self.response_capture = ResponseCapture()
        
        # Set up file system observer
        self.observer = Observer()
        self.observer.schedule(
            EnhancedBridgeOutboxHandler(self),
            self.config["paths"]["bridge_outbox"],
            recursive=False
        )
        self.observer.start()
        
        # Initialize agent regions
        self.agent_regions = {}
        self._load_agent_regions()
        
    def _load_agent_regions(self):
        """Load agent screen regions from config."""
        try:
            regions_path = Path(self.config["paths"]["runtime"]) / "agent_regions.json"
            if regions_path.exists():
                with open(regions_path) as f:
                    self.agent_regions = json.load(f)
        except Exception as e:
            logger.error(f"Error loading agent regions: {e}")
            
    def _save_agent_regions(self):
        """Save agent screen regions to config."""
        try:
            regions_path = Path(self.config["paths"]["runtime"]) / "agent_regions.json"
            with open(regions_path, 'w') as f:
                json.dump(self.agent_regions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving agent regions: {e}")
            
    def _create_response_processor(self) -> ResponseProcessor:
        """Create the response processor implementation.
        
        Returns:
            ResponseProcessor instance
        """
        return ResponseProcessorFactory.create_processor(ProcessorMode.CORE)
        
    def _get_response_files(self) -> List[Path]:
        """Get all response files to process.
        
        Returns:
            List of response file paths
        """
        return list(self.bridge_outbox.glob("*.json"))
        
    async def _check_completion(self, agent_id: str) -> Tuple[bool, str]:
        """Check if agent response is complete using hybrid detection.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Tuple of (is_complete, detection_method)
        """
        # 1. Check bridge outbox
        outbox_path = Path(self.config["paths"]["bridge_outbox"]) / f"agent-{agent_id}.json"
        if outbox_path.exists():
            try:
                with open(outbox_path) as f:
                    data = json.load(f)
                if data.get("status") == "complete":
                    return True, "outbox"
            except Exception as e:
                logger.error(f"Error reading outbox for {agent_id}: {e}")
                
        # 2. Check visual stability
        if agent_id in self.agent_regions:
            region = self.agent_regions[agent_id]
            if self._has_region_stabilized(region):
                return True, "visual"
                
        return False, "none"
        
    def _has_region_stabilized(self, region: Dict[str, Any], duration: int = 5) -> bool:
        """Check if screen region has stabilized.
        
        Args:
            region: Screen region coordinates
            duration: Duration in seconds to check stability
            
        Returns:
            True if region is stable
        """
        try:
            # Get initial hash
            prev_hash = self._hash_region(region)
            
            # Check stability over duration
            for _ in range(duration):
                time.sleep(1)
                curr_hash = self._hash_region(region)
                if curr_hash != prev_hash:
                    return False
                prev_hash = curr_hash
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking region stability: {e}")
            return False
            
    def _hash_region(self, region: Dict[str, Any]) -> str:
        """Compute hash of screen region.
        
        Args:
            region: Screen region coordinates
            
        Returns:
            Hash of region
        """
        try:
            # Calculate region dimensions
            x = region["top_left"]["x"]
            y = region["top_left"]["y"]
            width = region["bottom_right"]["x"] - x
            height = region["bottom_right"]["y"] - y
            
            # Capture region
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            if not screenshot:
                return ""
                
            # Convert to grayscale
            img_array = np.array(screenshot)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Compute hash
            return hashlib.sha256(gray.tobytes()).hexdigest()
            
        except Exception as e:
            logger.error(f"Error hashing region: {e}")
            return ""
            
    async def _resume_agent_impl(self, agent_id: str) -> bool:
        """Implementation-specific agent resume logic.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate agent state
            if not self.validation_engine.validate_agent_state(agent_id):
                return False
                
            # Resume agent
            return await self.validation_engine.resume_agent(agent_id)
            
        except Exception as e:
            logger.error(f"Error resuming agent {agent_id}: {e}")
            return False

class EnhancedBridgeOutboxHandler(FileSystemEventHandler):
    """Enhanced handler for bridge outbox events."""
    
    def __init__(self, daemon: EnhancedResponseLoopDaemon):
        """Initialize the handler.
        
        Args:
            daemon: Response loop daemon instance
        """
        self.daemon = daemon
        
    def on_created(self, event):
        """Handle file creation event.
        
        Args:
            event: File system event
        """
        if event.is_directory or not event.src_path.endswith('.json'):
            return
            
        asyncio.create_task(
            self.daemon._process_response_file(Path(event.src_path))
        ) 