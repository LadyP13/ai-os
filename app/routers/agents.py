"""
Agent management routes for AI-OS.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import (
    get_current_user,
    require_human,
    create_access_token,
    AGENT_TOKEN_EXPIRE_DAYS
)
from app.database import get_db
from app.models import Agent, User
from app.agent_runner import agent_registry

router = APIRouter(prefix="/agents", tags=["agents"])


def agent_to_dict(agent: Agent, is_running: bool = False) -> dict:
    return {
        "id": agent.id,
        "name": agent.name,
        "user_id": agent.user_id,
        "status": "running" if is_running else agent.status,
        "last_seen": agent.last_seen.isoformat() if agent.last_seen else None,
        "soul_file": agent.soul_file,
        "config_json": agent.config_json
    }


@router.get("")
async def list_agents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all agents."""
    agents = db.query(Agent).all()
    return [
        agent_to_dict(agent, agent_registry.is_running(agent.id))
        for agent in agents
    ]


@router.get("/{agent_id}")
async def get_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get agent details and status."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent_to_dict(agent, agent_registry.is_running(agent_id))


@router.post("/{agent_id}/start")
async def start_agent(
    agent_id: int,
    current_user: User = Depends(require_human),
    db: Session = Depends(get_db)
):
    """Start an agent loop (human only)."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent_registry.is_running(agent_id):
        return {"message": "Agent is already running", "status": "running"}

    runner = agent_registry.get_or_create(agent_id)
    runner.start()

    return {"message": "Agent started", "status": "running"}


@router.post("/{agent_id}/stop")
async def stop_agent(
    agent_id: int,
    current_user: User = Depends(require_human),
    db: Session = Depends(get_db)
):
    """Stop an agent loop (human only)."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    runner = agent_registry.get(agent_id)
    if not runner or not runner.running:
        return {"message": "Agent is not running", "status": "stopped"}

    runner.stop()
    return {"message": "Agent stopped", "status": "stopped"}


@router.get("/{agent_id}/token", tags=["auth"])
async def get_agent_token(
    agent_id: int,
    current_user: User = Depends(require_human),
    db: Session = Depends(get_db)
):
    """
    Get a long-lived token for an AI agent (human only, for setup).
    Also exposed at /api/agent-token/{agent_id} via server.py alias.
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    token_data = {
        "sub": agent.user.username,
        "role": "agent",
        "agent_id": agent_id
    }
    token = create_access_token(
        data=token_data,
        expires_delta=timedelta(days=AGENT_TOKEN_EXPIRE_DAYS)
    )

    return {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "access_token": token,
        "token_type": "bearer",
        "expires_days": AGENT_TOKEN_EXPIRE_DAYS
    }
