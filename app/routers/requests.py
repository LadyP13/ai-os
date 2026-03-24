"""
Approval request routes for AI-OS.
"""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_human, require_agent
from app.database import get_db
from app.models import User, Agent, ApprovalRequest
from app.ws_manager import ws_manager

router = APIRouter(prefix="/requests", tags=["requests"])


class CreateRequestBody(BaseModel):
    request_type: str
    description: str
    detail_json: Optional[dict] = None


class ResolveRequestBody(BaseModel):
    status: str  # "approved" or "denied"


def request_to_dict(req: ApprovalRequest, agent_name: Optional[str] = None) -> dict:
    return {
        "id": req.id,
        "agent_id": req.agent_id,
        "agent_name": agent_name,
        "request_type": req.request_type,
        "description": req.description,
        "detail_json": json.loads(req.detail_json) if req.detail_json else None,
        "status": req.status,
        "created_at": req.created_at.isoformat() if req.created_at else None,
        "resolved_at": req.resolved_at.isoformat() if req.resolved_at else None
    }


@router.get("")
async def list_requests(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List approval requests. Optional ?status=pending|approved|denied filter."""
    query = db.query(ApprovalRequest)
    if status:
        query = query.filter(ApprovalRequest.status == status)
    requests = query.order_by(ApprovalRequest.created_at.desc()).all()

    result = []
    for req in requests:
        agent = db.query(Agent).filter(Agent.id == req.agent_id).first()
        agent_name = agent.name if agent else None
        result.append(request_to_dict(req, agent_name))
    return result


@router.post("")
async def create_request(
    body: CreateRequestBody,
    current_user: User = Depends(require_agent),
    db: Session = Depends(get_db)
):
    """Create a new approval request (AI agent only)."""
    # Find the agent record for this user
    agent = db.query(Agent).filter(Agent.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent record not found for this user")

    req = ApprovalRequest(
        agent_id=agent.id,
        request_type=body.request_type,
        description=body.description,
        detail_json=json.dumps(body.detail_json) if body.detail_json else None,
        status="pending"
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    req_data = request_to_dict(req, agent.name)

    # Broadcast to WebSocket clients
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(ws_manager.broadcast({
                "type": "new_request",
                "request": req_data
            }))
    except Exception:
        pass

    return req_data


@router.put("/{request_id}")
async def resolve_request(
    request_id: int,
    body: ResolveRequestBody,
    current_user: User = Depends(require_human),
    db: Session = Depends(get_db)
):
    """Resolve an approval request: approved or denied (human only)."""
    if body.status not in ("approved", "denied"):
        raise HTTPException(status_code=400, detail="Status must be 'approved' or 'denied'")

    req = db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Request is already {req.status}")

    req.status = body.status
    req.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(req)

    agent = db.query(Agent).filter(Agent.id == req.agent_id).first()
    req_data = request_to_dict(req, agent.name if agent else None)

    # Broadcast resolution to WebSocket clients
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(ws_manager.broadcast({
                "type": "request_resolved",
                "request_id": request_id,
                "status": body.status,
                "request": req_data
            }))
    except Exception:
        pass

    return req_data
