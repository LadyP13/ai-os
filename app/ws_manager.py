"""
WebSocket connection manager for AI-OS.
Handles broadcasting messages to all connected clients.
"""

import json
from typing import List, Dict, Any

from fastapi import WebSocket


class WebSocketManager:
    """Manages active WebSocket connections and broadcasts."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: Dict[str, Any]):
        """Broadcast a JSON message to all connected clients."""
        message = json.dumps(data)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal_message(self, websocket: WebSocket, data: Dict[str, Any]):
        """Send a message to a specific WebSocket client."""
        try:
            await websocket.send_text(json.dumps(data))
        except Exception:
            self.disconnect(websocket)


# Global singleton
ws_manager = WebSocketManager()
