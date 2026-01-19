"""
WebSocket API endpoints for real-time features.
"""
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        # room_id -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        """Accept and register a new connection."""
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)
        logger.info(f"WebSocket connected to room {room_id}")

    def disconnect(self, websocket: WebSocket, room_id: str):
        """Remove a connection."""
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        logger.info(f"WebSocket disconnected from room {room_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to a specific connection."""
        await websocket.send_json(message)

    async def broadcast(self, message: dict, room_id: str):
        """Broadcast message to all connections in a room."""
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")

    def get_connection_count(self, room_id: str) -> int:
        """Get number of connections in a room."""
        return len(self.active_connections.get(room_id, set()))


manager = ConnectionManager()


@router.websocket("/live/{room_id}")
async def live_danmaku_websocket(websocket: WebSocket, room_id: str):
    """
    WebSocket endpoint for real-time live stream danmaku.
    实时弹幕WebSocket
    """
    await manager.connect(websocket, room_id)
    try:
        while True:
            # Receive messages from client (e.g., heartbeat)
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)


@router.websocket("/task/{task_id}")
async def task_log_websocket(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time task logs.
    任务日志实时推送
    """
    await manager.connect(websocket, f"task_{task_id}")
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, f"task_{task_id}")
