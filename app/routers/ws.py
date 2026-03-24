"""
WebSocket endpoint for AI-OS real-time communication.
"""

import json
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User, Message
from app.ws_manager import ws_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(default=None)
):
    """
    WebSocket endpoint for real-time updates.
    Accepts a ?token= query parameter for auth.
    """
    # Authenticate via token
    user = None
    if token:
        db = SessionLocal()
        try:
            from app.auth import get_user_from_token
            user = get_user_from_token(token, db)
        finally:
            db.close()

    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await ws_manager.connect(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            if msg_type == "send_message":
                content = data.get("content", "").strip()
                if not content:
                    continue

                db = SessionLocal()
                try:
                    msg = Message(
                        sender_role=user.role,
                        sender_name=user.username,
                        content=content,
                        message_type="chat"
                    )
                    db.add(msg)
                    db.commit()
                    db.refresh(msg)

                    msg_data = {
                        "id": msg.id,
                        "sender_role": msg.sender_role,
                        "sender_name": msg.sender_name,
                        "content": msg.content,
                        "message_type": msg.message_type,
                        "created_at": msg.created_at.isoformat() if msg.created_at else None,
                        "read_at": msg.read_at.isoformat() if msg.read_at else None
                    }
                finally:
                    db.close()

                # Broadcast to all clients
                await ws_manager.broadcast({
                    "type": "new_message",
                    "message": msg_data
                })

            elif msg_type == "ping":
                await ws_manager.send_personal_message(websocket, {"type": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
