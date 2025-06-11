"""
Cursor Bridge Implementation
--------------------------
Bridge implementation for Cursor UI automation.
"""

import os
import json
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ..base.bridge import BaseBridge, BridgeConfig, BridgeError, ErrorSeverity

logger = logging.getLogger(__name__)

class CursorBridge(BaseBridge):
    """Bridge implementation for Cursor UI automation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Cursor bridge.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        
        # Set up paths
        self.bridge_dir = Path(self.config.get("paths", {}).get("bridge_dir", "data/bridge"))
        self.bridge_dir.mkdir(parents=True, exist_ok=True)
        
        # C# bridge executable path
        self.bridge_exe = Path(self.config.get("bridge_exe", "bridge/cursor_bridge/CursorBridge.exe"))
        if not self.bridge_exe.exists():
            raise FileNotFoundError(f"Cursor bridge executable not found: {self.bridge_exe}")
            
        # Response file path
        self.response_file = self.bridge_dir / "cursor_response.json"
        
        # Bridge process
        self._process: Optional[subprocess.Popen] = None
        
    async def start(self) -> None:
        """Start the bridge."""
        if self.is_running:
            return
            
        try:
            # Start C# bridge process
            self._process = subprocess.Popen(
                [str(self.bridge_exe), str(self.response_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            self.is_running = True
            logger.info("Started Cursor bridge")
            
        except Exception as e:
            error = BridgeError(
                f"Failed to start Cursor bridge: {str(e)}",
                severity=ErrorSeverity.ERROR,
                context={"exe_path": str(self.bridge_exe)},
                correlation_id=self._correlation_id
            )
            logger.error(str(error))
            raise error
            
    async def stop(self) -> None:
        """Stop the bridge."""
        if not self.is_running:
            return
            
        try:
            if self._process:
                self._process.terminate()
                await asyncio.sleep(1)  # Give it time to clean up
                if self._process.poll() is None:
                    self._process.kill()
                self._process = None
                
            self.is_running = False
            logger.info("Stopped Cursor bridge")
            
        except Exception as e:
            error = BridgeError(
                f"Error stopping Cursor bridge: {str(e)}",
                severity=ErrorSeverity.ERROR,
                correlation_id=self._correlation_id
            )
            logger.error(str(error))
            raise error
            
    async def send_message(
        self,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a message through the bridge.
        
        Args:
            message: Message to send
            metadata: Optional metadata
            
        Returns:
            Response dictionary
        """
        if not self.is_running:
            raise BridgeError(
                "Bridge is not running",
                severity=ErrorSeverity.ERROR,
                correlation_id=self._correlation_id
            )
            
        try:
            # Write message to file for C# bridge to pick up
            message_file = self.bridge_dir / "cursor_message.json"
            with open(message_file, "w") as f:
                json.dump({
                    "message": message,
                    "metadata": metadata or {},
                    "timestamp": datetime.utcnow().isoformat()
                }, f)
                
            # Wait for response
            response = await self._wait_for_response()
            if not response:
                raise BridgeError(
                    "No response received from Cursor bridge",
                    severity=ErrorSeverity.ERROR,
                    correlation_id=self._correlation_id
                )
                
            return response
            
        except Exception as e:
            error = BridgeError(
                f"Error sending message: {str(e)}",
                severity=ErrorSeverity.ERROR,
                context={"message": message},
                correlation_id=self._correlation_id
            )
            logger.error(str(error))
            raise error
            
    async def receive_message(
        self,
        timeout: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Receive a message from the bridge.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            Message dictionary or None if timeout
        """
        if not self.is_running:
            raise BridgeError(
                "Bridge is not running",
                severity=ErrorSeverity.ERROR,
                correlation_id=self._correlation_id
            )
            
        try:
            return await self._wait_for_response(timeout)
        except Exception as e:
            error = BridgeError(
                f"Error receiving message: {str(e)}",
                severity=ErrorSeverity.ERROR,
                correlation_id=self._correlation_id
            )
            logger.error(str(error))
            raise error
            
    async def _wait_for_response(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Wait for a response from the C# bridge.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            Response dictionary or None if timeout
        """
        start_time = datetime.now()
        while True:
            if timeout and (datetime.now() - start_time).total_seconds() > timeout:
                return None
                
            if self.response_file.exists():
                try:
                    with open(self.response_file, "r") as f:
                        response = json.load(f)
                    os.remove(self.response_file)  # Clean up
                    return response
                except json.JSONDecodeError:
                    pass
                    
            await asyncio.sleep(0.1)  # Poll every 100ms
            
    async def validate_response(
        self,
        response: Dict[str, Any]
    ) -> bool:
        """Validate a response.
        
        Args:
            response: Response to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = {"timestamp", "content", "source"}
        return all(field in response for field in required_fields)
        
    async def get_health(self) -> Dict[str, Any]:
        """Get bridge health status.
        
        Returns:
            Health status dictionary
        """
        return {
            "running": self.is_running,
            "process_alive": self._process is not None and self._process.poll() is None,
            "response_file_exists": self.response_file.exists()
        }
        
    async def get_metrics(self) -> Dict[str, Any]:
        """Get bridge metrics.
        
        Returns:
            Metrics dictionary
        """
        return {
            "start_time": self.start_time.isoformat(),
            "uptime": (datetime.now() - self.start_time).total_seconds()
        } 