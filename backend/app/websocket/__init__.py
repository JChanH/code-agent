"""WebSocket connection manager for real-time agent updates."""

from fastapi import WebSocket
from typing import Any
import json
import asyncio


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages to clients."""

    def __init__(self):
        # project_id -> list of connected websockets
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: str) -> None:
        await websocket.accept()
        if project_id not in self._connections:
            self._connections[project_id] = []
        self._connections[project_id].append(websocket)

    def disconnect(self, websocket: WebSocket, project_id: str) -> None:
        if project_id in self._connections:
            self._connections[project_id] = [
                ws for ws in self._connections[project_id] if ws != websocket
            ]
            if not self._connections[project_id]:
                del self._connections[project_id]

    async def broadcast(self, project_id: str, message: dict[str, Any]) -> None:
        """Send a message to all clients connected to a project."""
        if project_id not in self._connections:
            return

        payload = json.dumps(message, ensure_ascii=False, default=str)
        dead: list[WebSocket] = []

        for ws in self._connections[project_id]:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        # Clean up dead connections
        for ws in dead:
            self.disconnect(ws, project_id)

    async def send_to(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        """Send a message to a specific client."""
        payload = json.dumps(message, ensure_ascii=False, default=str)
        await websocket.send_text(payload)

    @property
    def connection_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


# Singleton instance
ws_manager = ConnectionManager()
