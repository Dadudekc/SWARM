"""
WebSocket Server
--------------
FastAPI WebSocket server for real-time response streaming.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and broadcasting."""
    
    def __init__(self):
        """Initialize manager."""
        self.app = FastAPI(title="Dream.OS Response Server")
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.loop = asyncio.get_event_loop()
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # TODO: Configure for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add routes
        self.app.websocket("/agents/{agent_id}")(self.websocket_endpoint)
        
    async def connect(self, websocket: WebSocket, agent_id: str):
        """Connect WebSocket client.
        
        Args:
            websocket: WebSocket connection
            agent_id: Agent identifier
        """
        await websocket.accept()
        if agent_id not in self.active_connections:
            self.active_connections[agent_id] = set()
        self.active_connections[agent_id].add(websocket)
        logger.info(f"Client connected to agent {agent_id}")
        
    def disconnect(self, websocket: WebSocket, agent_id: str):
        """Disconnect WebSocket client.
        
        Args:
            websocket: WebSocket connection
            agent_id: Agent identifier
        """
        if agent_id in self.active_connections:
            self.active_connections[agent_id].discard(websocket)
            if not self.active_connections[agent_id]:
                del self.active_connections[agent_id]
        logger.info(f"Client disconnected from agent {agent_id}")
        
    async def broadcast_response(self, agent_id: str, response: dict):
        """Broadcast response to agent's clients.
        
        Args:
            agent_id: Agent identifier
            response: Response to broadcast
        """
        if agent_id not in self.active_connections:
            return
            
        # Convert response to JSON
        try:
            message = json.dumps(response)
        except Exception as e:
            logger.error(f"Failed to serialize response: {e}")
            return
            
        # Broadcast to all clients
        disconnected = set()
        for websocket in self.active_connections[agent_id]:
            try:
                await websocket.send_text(message)
            except WebSocketDisconnect:
                disconnected.add(websocket)
            except Exception as e:
                logger.error(f"Failed to send response: {e}")
                disconnected.add(websocket)
                
        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket, agent_id)
            
    async def websocket_endpoint(self, websocket: WebSocket, agent_id: str):
        """WebSocket endpoint for agent.
        
        Args:
            websocket: WebSocket connection
            agent_id: Agent identifier
        """
        await self.connect(websocket, agent_id)
        try:
            while True:
                # Wait for messages (can be used for client->server communication)
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    # TODO: Handle client messages
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from client: {data}")
                    
        except WebSocketDisconnect:
            self.disconnect(websocket, agent_id)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.disconnect(websocket, agent_id)
            
    def run(self, host: str = "localhost", port: int = 8000):
        """Run the server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        import uvicorn
        uvicorn.run(self.app, host=host, port=port) 