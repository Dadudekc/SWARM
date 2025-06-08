"""
WebSocket Telemetry Server
-------------------------
Real-time agent status broadcasting via WebSocket.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Set, Dict, Any
import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)

class TelemetryServer:
    """WebSocket server for broadcasting agent telemetry."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        """Initialize the telemetry server.
        
        Args:
            host: Server host address
            port: Server port
        """
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.agent_status: Dict[str, Dict[str, Any]] = {}
        
    async def handler(self, websocket: WebSocketServerProtocol, path: str):
        """Handle WebSocket connections.
        
        Args:
            websocket: WebSocket connection
            path: Request path
        """
        self.clients.add(websocket)
        try:
            # Send current state to new client
            if self.agent_status:
                await websocket.send(json.dumps({
                    "type": "state",
                    "data": self.agent_status
                }))
                
            # Keep connection alive
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get("type") == "heartbeat":
                        await self._handle_heartbeat(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.debug("Client disconnected")
        finally:
            self.clients.discard(websocket)
            
    async def _handle_heartbeat(self, data: Dict[str, Any]):
        """Handle agent heartbeat.
        
        Args:
            data: Heartbeat data
        """
        agent_id = data.get("agent")
        if not agent_id:
            return
            
        # Update agent status
        self.agent_status[agent_id] = {
            "status": data.get("status", "unknown"),
            "ts": datetime.utcnow().isoformat(),
            "data": data.get("data", {})
        }
        
        # Broadcast to all clients
        await self.broadcast({
            "type": "heartbeat",
            "data": self.agent_status[agent_id]
        })
        
    async def broadcast(self, data: Dict[str, Any]):
        """Broadcast data to all connected clients.
        
        Args:
            data: Data to broadcast
        """
        if not self.clients:
            return
            
        payload = json.dumps(data)
        websockets_to_remove = set()
        
        for websocket in self.clients:
            try:
                await websocket.send(payload)
            except websockets.exceptions.ConnectionClosed:
                websockets_to_remove.add(websocket)
                
        # Clean up dead connections
        self.clients -= websockets_to_remove
        
    async def start(self):
        """Start the WebSocket server."""
        server = await websockets.serve(
            self.handler,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        )
        logger.info(f"Telemetry server started on ws://{self.host}:{self.port}")
        return server

# Global instance
TELEMETRY = TelemetryServer()

def start_server():
    """Start the telemetry server."""
    loop = asyncio.get_event_loop()
    server = loop.run_until_complete(TELEMETRY.start())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_server() 