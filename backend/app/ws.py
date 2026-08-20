from __future__ import annotations

from fastapi import WebSocket

from .schemas import SnipeOut


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, snipe: SnipeOut) -> None:
        if not self._connections:
            return
        payload = snipe.model_dump(mode="json")
        stale: set[WebSocket] = set()
        for websocket in self._connections:
            try:
                await websocket.send_json(payload)
            except Exception:
                stale.add(websocket)
        self._connections -= stale
