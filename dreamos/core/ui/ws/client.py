"""
WebSocket Client
--------------
Example WebSocket client for receiving responses.
"""

import asyncio
import json
import logging
import websockets
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class ResponseClient:
    """WebSocket client for receiving responses."""
    
    def __init__(
        self,
        agent_id: str,
        host: str = "localhost",
        port: int = 8000,
        on_response: Optional[Callable[[dict], None]] = None
    ):
        """Initialize client.
        
        Args:
            agent_id: Agent identifier
            host: Server host
            port: Server port
            on_response: Callback for responses
        """
        self.agent_id = agent_id
        self.url = f"ws://{host}:{port}/agents/{agent_id}"
        self.on_response = on_response
        self._running = False
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        
    async def connect(self):
        """Connect to server."""
        try:
            self._websocket = await websockets.connect(self.url)
            logger.info(f"Connected to {self.url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
            
    async def disconnect(self):
        """Disconnect from server."""
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
            logger.info("Disconnected from server")
            
    async def start(self):
        """Start receiving responses."""
        if self._running:
            return
            
        if not await self.connect():
            return
            
        self._running = True
        try:
            while self._running:
                try:
                    # Receive message
                    message = await self._websocket.recv()
                    
                    # Parse response
                    try:
                        response = json.loads(message)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON: {message}")
                        continue
                        
                    # Call callback
                    if self.on_response:
                        self.on_response(response)
                        
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Connection closed")
                    break
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    break
                    
        finally:
            self._running = False
            await self.disconnect()
            
    def stop(self):
        """Stop receiving responses."""
        self._running = False
        
async def main():
    """Example usage."""
    def on_response(response: dict):
        """Handle response."""
        print(f"Received response: {json.dumps(response, indent=2)}")
        
    # Create client
    client = ResponseClient("agent-1", on_response=on_response)
    
    try:
        # Start receiving
        await client.start()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        client.stop()
        
if __name__ == "__main__":
    asyncio.run(main()) 