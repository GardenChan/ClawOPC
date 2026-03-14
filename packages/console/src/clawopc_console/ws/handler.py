"""WebSocket handler for real-time workspace updates.

Pushes workspace state changes to connected Console clients
when file changes are detected by the FileWatcher.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Connected clients
_clients: set[WebSocket] = set()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time updates.

    Clients connect here to receive push notifications about:
      - Agent state changes
      - New tasks awaiting decision
      - Task status transitions
    """
    await websocket.accept()
    _clients.add(websocket)

    try:
        while True:
            # Keep the connection alive; we push data, not receive
            # Client can send ping/pong or simple keepalive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        _clients.discard(websocket)
    except Exception:
        _clients.discard(websocket)


async def broadcast(event: str, payload: dict) -> None:
    """Broadcast an event to all connected WebSocket clients.

    Args:
        event: Event type string (e.g. 'state_change', 'new_decision').
        payload: Event data to send.
    """
    if not _clients:
        return

    message = json.dumps({"event": event, "data": payload})
    disconnected: list[WebSocket] = []

    for client in _clients:
        try:
            await client.send_text(message)
        except Exception:
            disconnected.append(client)

    for client in disconnected:
        _clients.discard(client)
