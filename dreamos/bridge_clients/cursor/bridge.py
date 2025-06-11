import subprocess
import json
import os
import time
import asyncio
from typing import Dict, Any, Optional
from dreamos.core.bridge.base import BaseBridge
from dreamos.core.errors.bridge_errors import BridgeError

class CursorBridge(BaseBridge):
    def __init__(self, exe_path="dreamos/bridge_clients/CursorBridge/bin/Debug/net8.0/CursorBridge.exe"):
        super().__init__(config={})  # Initialize with empty config for now
        self.exe_path = exe_path
        self.output_file = os.path.join(os.path.dirname(exe_path), "cursor_response.json")
        self.is_running = False

    async def start(self) -> None:
        """Start the bridge."""
        if self.is_running:
            return
        self.is_running = True

    async def stop(self) -> None:
        """Stop the bridge."""
        self.is_running = False

    async def send_message(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a message through the bridge."""
        if not self.is_running:
            raise BridgeError("Bridge is not running", severity="high")
        
        # Clean up any stale output
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

        # Run the C# executable
        try:
            subprocess.run([self.exe_path], check=True)
        except Exception as e:
            raise BridgeError(f"Failed to run C# bridge: {e}", severity="high")

        # Wait for output file
        for _ in range(20):  # wait up to ~2 seconds
            if os.path.exists(self.output_file):
                break
            await asyncio.sleep(0.1)
        else:
            raise BridgeError("No output received from CursorBridge.", severity="high")

        # Read and return the response
        try:
            with open(self.output_file, "r") as f:
                data = json.load(f)
            return {"response": data.get("response", "")}
        except Exception as e:
            raise BridgeError(f"Failed to parse cursor response: {e}", severity="medium")

    async def receive_message(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Receive a message from the bridge."""
        if not os.path.exists(self.output_file):
            return None
            
        try:
            with open(self.output_file, "r") as f:
                data = json.load(f)
            return {"response": data.get("response", "")}
        except Exception as e:
            raise BridgeError(f"Failed to parse cursor response: {e}", severity="medium")

    async def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate a response."""
        return isinstance(response, dict) and "response" in response

    async def get_health(self) -> Dict[str, Any]:
        """Get bridge health status."""
        return {
            "status": "healthy" if self.is_running else "stopped",
            "exe_exists": os.path.exists(self.exe_path),
            "output_exists": os.path.exists(self.output_file)
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """Get bridge metrics."""
        return {
            "is_running": self.is_running,
            "exe_path": self.exe_path,
            "output_file": self.output_file
        }

if __name__ == "__main__":
    bridge = CursorBridge()
    print("Captured:", bridge.capture_response()) 