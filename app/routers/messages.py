"""
Message routes for AI-OS.
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User, Message
from app.ws_manager import ws_manager

router = APIRouter(prefix="/messages", tags=["messages"])


class SendMessageRequest(BaseModel):
    content: str
    message_type: Optional[str] = "chat"


def message_to_dict(msg: Message) -> dict:
    return {
        "id": msg.id,
        "sender_role": msg.sender_role,
        "sender_name": msg.sender_name,
        "content": msg.content,
        "message_type": msg.message_type,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
        "read_at": msg.read_at.isoformat() if msg.read_at else None
    }


@router.get("")
async def get_messages(
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get message history (last N messages)."""
    messages = (
        db.query(Message)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    # Return in chronological order
    messages.reverse()
    return [message_to_dict(m) for m in messages]


@router.post("")
async def send_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message."""
    msg = Message(
        sender_role=current_user.role,
        sender_name=current_user.username,
        content=request.content,
        message_type=request.message_type or "chat"
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    msg_data = message_to_dict(msg)

    # Broadcast to WebSocket clients
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(ws_manager.broadcast({
                "type": "new_message",
                "message": msg_data
            }))
    except Exception:
        pass

    return msg_data
