"""
Permission management routes for AI-OS.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_human
from app.database import get_db
from app.models import User, Agent, Permission
from app.permissions_config import PERMISSIONS

router = APIRouter(prefix="/permissions", tags=["permissions"])


def permission_to_dict(perm: Permission) -> dict:
    config = PERMISSIONS.get(perm.permission_key, {})
    return {
        "id": perm.id,
        "agent_id": perm.agent_id,
        "permission_key": perm.permission_key,
        "enabled": perm.enabled,
        "updated_at": perm.updated_at.isoformat() if perm.updated_at else None,
        "label": config.get("label", perm.permission_key),
        "description": config.get("description", ""),
        "icon": config.get("icon", "")
    }


class TogglePermissionRequest(BaseModel):
    enabled: bool


@router.get("/{agent_id}")
async def get_permissions(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all permissions for an agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    permissions = db.query(Permission).filter(Permission.agent_id == agent_id).all()
    return [permission_to_dict(p) for p in permissions]


@router.put("/{agent_id}/{key}")
async def toggle_permission(
    agent_id: int,
    key: str,
    request: TogglePermissionRequest,
    current_user: User = Depends(require_human),
    db: Session = Depends(get_db)
):
    """Toggle a permission for an agent (human only)."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if key not in PERMISSIONS:
        raise HTTPException(status_code=400, detail=f"Unknown permission key: {key}")

    perm = db.query(Permission).filter(
        Permission.agent_id == agent_id,
        Permission.permission_key == key
    ).first()

    if perm:
        perm.enabled = request.enabled
        perm.updated_at = datetime.utcnow()
    else:
        perm = Permission(
            agent_id=agent_id,
            permission_key=key,
            enabled=request.enabled
        )
        db.add(perm)

    db.commit()
    db.refresh(perm)

    return permission_to_dict(perm)
