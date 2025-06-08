"""
WebSocket Telemetry Client
-------------------------
Client for receiving real-time agent telemetry updates.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable
import websockets
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class WSClient(QObject):
    """WebSocket client for receiving telemetry updates."""
    
    # Signals
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    heartbeat = pyqtSignal(dict)  # Emits heartbeat data
    error = pyqtSignal(str)       # Emits error messages
    
    def __init__(self, url: str = "ws://127.0.0.1:8765"):
        """Initialize the WebSocket client.
        
        Args:
            url: WebSocket server URL
        """
        super().__init__()
        self.url = url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.url)
            self._running = True
            self.connected.emit()
            logger.info(f"Connected to {self.url}")
            
            # Start message loop
            while self._running:
                try:
                    message = await self.websocket.recv()
                    data = json.loads(message)
                    
                    if data.get("type") == "heartbeat":
                        self.heartbeat.emit(data["data"])
                    elif data.get("type") == "state":
                        # Handle initial state
                        for agent_data in data["data"].values():
                            self.heartbeat.emit(agent_data)
                            
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("Connection closed")
                    break
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")
                    
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.error.emit(str(e))
        finally:
            self._running = False
            self.disconnected.emit()
            
    def start(self):
        """Start the WebSocket client in a new event loop."""
        def run_client():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self.connect())
            
        # Start in a new thread
        import threading
        thread = threading.Thread(target=run_client, daemon=True)
        thread.start()
        
    def stop(self):
        """Stop the WebSocket client."""
        self._running = False
        if self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.websocket.close(),
                self._loop
            )
            
    def send(self, data: Dict[str, Any]):
        """Send data to the WebSocket server.
        
        Args:
            data: Data to send
        """
        if not self.websocket:
            return
            
        asyncio.run_coroutine_threadsafe(
            self.websocket.send(json.dumps(data)),
            self._loop
        ) 