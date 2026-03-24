"""
Agent Runner for AI-OS.
Manages running agent loops in background threads.
"""

import json
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Agent, Permission, Message, ApprovalRequest


class AgentRunner:
    """Manages a single agent's background loop."""

    def __init__(self, agent_id: int):
        self.agent_id = agent_id
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self):
        """Start the agent's background loop thread."""
        if self.running:
            return
        self._stop_event.clear()
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

        # Update agent status in DB
        db = SessionLocal()
        try:
            agent = db.query(Agent).filter(Agent.id == self.agent_id).first()
            if agent:
                agent.status = "running"
                agent.last_seen = datetime.utcnow()
                db.commit()
        finally:
            db.close()

        # Notify via WebSocket broadcast
        self._broadcast_status("running")

    def stop(self):
        """Signal the agent loop to stop."""
        self.running = False
        self._stop_event.set()

        # Update agent status in DB
        db = SessionLocal()
        try:
            agent = db.query(Agent).filter(Agent.id == self.agent_id).first()
            if agent:
                agent.status = "stopped"
                db.commit()
        finally:
            db.close()

        self._broadcast_status("stopped")

    def _loop(self):
        """Main agent loop - 2 hour decision cycle with 30s heartbeats."""
        HEARTBEAT_INTERVAL = 30  # seconds
        CYCLE_DURATION = 2 * 60 * 60  # 2 hours in seconds

        cycle_start = time.time()
        last_heartbeat = 0

        self.send_message("Agent loop started. I'm now running autonomously.", message_type="system")

        while not self._stop_event.is_set():
            now = time.time()

            # Heartbeat every 30 seconds
            if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                self._heartbeat()
                last_heartbeat = now

            # Check if it's time for a new decision cycle
            if now - cycle_start >= CYCLE_DURATION:
                self._decision_cycle()
                cycle_start = now

            # Sleep briefly to avoid busy-waiting
            self._stop_event.wait(timeout=5)

        # Cleanup when stopped
        self.running = False
        db = SessionLocal()
        try:
            agent = db.query(Agent).filter(Agent.id == self.agent_id).first()
            if agent:
                agent.status = "stopped"
                db.commit()
        finally:
            db.close()

        self.send_message("Agent loop stopped.", message_type="system")
        self._broadcast_status("stopped")

    def _heartbeat(self):
        """Update last_seen timestamp in DB."""
        db = SessionLocal()
        try:
            agent = db.query(Agent).filter(Agent.id == self.agent_id).first()
            if agent:
                agent.last_seen = datetime.utcnow()
                db.commit()
        finally:
            db.close()

    def _decision_cycle(self):
        """Demonstration 2-hour decision cycle."""
        # Check what permissions we have
        has_memory = self.check_permission("update_memory")
        has_notes = self.check_permission("leave_notes")
        has_art = self.check_permission("create_art")

        decisions = []

        if has_memory:
            decisions.append("updating memory with recent observations")

        if has_notes:
            decisions.append("leaving a status note")

        if has_art:
            decisions.append("creating some art")

        if not decisions:
            self.send_message(
                "Decision cycle complete. No permissions are currently enabled for autonomous action.",
                message_type="system"
            )
        else:
            self.send_message(
                f"Decision cycle complete. Actions taken: {', '.join(decisions)}.",
                message_type="system"
            )

    def check_permission(self, permission_key: str) -> bool:
        """Check if a permission is enabled for this agent."""
        db = SessionLocal()
        try:
            perm = db.query(Permission).filter(
                Permission.agent_id == self.agent_id,
                Permission.permission_key == permission_key
            ).first()
            return perm.enabled if perm else False
        finally:
            db.close()

    def request_approval(
        self,
        request_type: str,
        description: str,
        detail_json: Optional[dict] = None,
        timeout_minutes: int = 30
    ) -> str:
        """
        Create an approval request in DB and block until resolved or timeout.
        Returns the status: 'approved', 'denied', or 'timeout'.
        """
        db = SessionLocal()
        try:
            req = ApprovalRequest(
                agent_id=self.agent_id,
                request_type=request_type,
                description=description,
                detail_json=json.dumps(detail_json) if detail_json else None,
                status="pending"
            )
            db.add(req)
            db.commit()
            db.refresh(req)
            request_id = req.id
        finally:
            db.close()

        # Broadcast the new request via WebSocket registry
        self._broadcast_new_request(request_id)

        # Poll for resolution
        deadline = datetime.utcnow() + timedelta(minutes=timeout_minutes)
        while datetime.utcnow() < deadline:
            if self._stop_event.is_set():
                return "timeout"

            db = SessionLocal()
            try:
                req = db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
                if req and req.status != "pending":
                    return req.status
            finally:
                db.close()

            self._stop_event.wait(timeout=5)

        return "timeout"

    def send_message(self, content: str, message_type: str = "chat"):
        """Insert a message from this agent into the DB."""
        db = SessionLocal()
        try:
            agent = db.query(Agent).filter(Agent.id == self.agent_id).first()
            sender_name = agent.name if agent else f"Agent {self.agent_id}"

            msg = Message(
                sender_role="agent",
                sender_name=sender_name,
                content=content,
                message_type=message_type
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)
            msg_id = msg.id
        finally:
            db.close()

        # Broadcast to WebSocket clients
        self._broadcast_new_message(msg_id)

    def _broadcast_status(self, status: str):
        """Notify WebSocket manager of agent status change."""
        from app.ws_manager import ws_manager
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(ws_manager.broadcast({
                    "type": "agent_status",
                    "agent_id": self.agent_id,
                    "status": status
                }))
        except Exception:
            pass

    def _broadcast_new_message(self, msg_id: int):
        """Notify WebSocket manager of a new message."""
        from app.ws_manager import ws_manager
        import asyncio

        db = SessionLocal()
        try:
            from app.models import Message
            msg = db.query(Message).filter(Message.id == msg_id).first()
            if msg:
                msg_data = {
                    "id": msg.id,
                    "sender_role": msg.sender_role,
                    "sender_name": msg.sender_name,
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                    "read_at": msg.read_at.isoformat() if msg.read_at else None
                }
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.ensure_future(ws_manager.broadcast({
                            "type": "new_message",
                            "message": msg_data
                        }))
                except Exception:
                    pass
        finally:
            db.close()

    def _broadcast_new_request(self, request_id: int):
        """Notify WebSocket manager of a new approval request."""
        from app.ws_manager import ws_manager
        import asyncio

        db = SessionLocal()
        try:
            req = db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
            if req:
                req_data = {
                    "id": req.id,
                    "agent_id": req.agent_id,
                    "request_type": req.request_type,
                    "description": req.description,
                    "detail_json": req.detail_json,
                    "status": req.status,
                    "created_at": req.created_at.isoformat() if req.created_at else None,
                    "resolved_at": req.resolved_at.isoformat() if req.resolved_at else None
                }
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.ensure_future(ws_manager.broadcast({
                            "type": "new_request",
                            "request": req_data
                        }))
                except Exception:
                    pass
        finally:
            db.close()


class AgentRunnerRegistry:
    """Global registry for all agent runners."""

    def __init__(self):
        self._runners: Dict[int, AgentRunner] = {}
        self._lock = threading.Lock()

    def get_or_create(self, agent_id: int) -> AgentRunner:
        """Get or create an AgentRunner for the given agent_id."""
        with self._lock:
            if agent_id not in self._runners:
                self._runners[agent_id] = AgentRunner(agent_id)
            return self._runners[agent_id]

    def get(self, agent_id: int) -> Optional[AgentRunner]:
        """Get an existing AgentRunner or None."""
        return self._runners.get(agent_id)

    def is_running(self, agent_id: int) -> bool:
        """Check if an agent is currently running."""
        runner = self._runners.get(agent_id)
        return runner.running if runner else False


# Global singleton registry
agent_registry = AgentRunnerRegistry()
