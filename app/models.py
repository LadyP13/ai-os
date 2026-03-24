"""
SQLAlchemy models for AI-OS.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)  # "human" or "agent"
    hashed_password = Column(String, nullable=False)
    totp_secret = Column(String, nullable=True)
    totp_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="user", uselist=False)


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="stopped")  # "running", "paused", "stopped"
    last_seen = Column(DateTime, nullable=True)
    soul_file = Column(String, nullable=True)
    config_json = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="agent")
    permissions = relationship("Permission", back_populates="agent", cascade="all, delete-orphan")
    approval_requests = relationship("ApprovalRequest", back_populates="agent", cascade="all, delete-orphan")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    permission_key = Column(String, nullable=False)
    enabled = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="permissions")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_role = Column(String, nullable=False)  # "human" or "agent"
    sender_name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String, default="chat")  # "chat", "request", "system"
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    request_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    detail_json = Column(Text, nullable=True)
    status = Column(String, default="pending")  # "pending", "approved", "denied"
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    agent = relationship("Agent", back_populates="approval_requests")
