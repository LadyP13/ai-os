"""
Authentication routes for AI-OS.
"""

import base64
import io
from datetime import timedelta
from typing import Optional

import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    verify_password,
    hash_password,
    get_current_user,
    require_human,
    HUMAN_TOKEN_EXPIRE_HOURS,
    AGENT_TOKEN_EXPIRE_DAYS
)
from app.database import get_db
from app.models import User, Agent

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str
    totp_code: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str
    requires_2fa: bool = False


class Setup2FAResponse(BaseModel):
    qr_code: str  # base64 PNG
    secret: str
    otpauth_url: str


class Verify2FARequest(BaseModel):
    code: str


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with username + password. If 2FA enabled, also requires TOTP code."""
    user = db.query(User).filter(User.username == request.username).first()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Check 2FA requirement
    if user.totp_enabled:
        if not request.totp_code:
            # Signal to client that 2FA is required
            return {"requires_2fa": True, "access_token": None, "token_type": "bearer", "role": user.role, "username": user.username}

        # Verify TOTP code
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(request.totp_code, valid_window=1):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code"
            )

    # Generate token
    if user.role == "agent":
        expires = timedelta(days=AGENT_TOKEN_EXPIRE_DAYS)
    else:
        expires = timedelta(hours=HUMAN_TOKEN_EXPIRE_HOURS)

    # Get agent_id if user is an agent
    agent_id = None
    if user.role == "agent" and user.agent:
        agent_id = user.agent.id

    token_data = {
        "sub": user.username,
        "role": user.role,
        "agent_id": agent_id
    }
    access_token = create_access_token(data=token_data, expires_delta=expires)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
        "requires_2fa": False
    }


@router.post("/setup-2fa")
async def setup_2fa(
    current_user: User = Depends(require_human),
    db: Session = Depends(get_db)
):
    """Generate a TOTP secret and QR code for 2FA setup."""
    # Generate new secret
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    otpauth_url = totp.provisioning_uri(
        name=current_user.username,
        issuer_name="AI-OS"
    )

    # Store the secret (not enabled until verified)
    user = db.query(User).filter(User.id == current_user.id).first()
    user.totp_secret = secret
    db.commit()

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(otpauth_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return {
        "qr_code": qr_base64,
        "secret": secret,
        "otpauth_url": otpauth_url
    }


@router.post("/verify-2fa")
async def verify_2fa(
    request: Verify2FARequest,
    current_user: User = Depends(require_human),
    db: Session = Depends(get_db)
):
    """Verify TOTP code and enable 2FA on the account."""
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated. Call /api/auth/setup-2fa first."
        )

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(request.code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )

    user.totp_enabled = True
    db.commit()

    return {"message": "2FA enabled successfully"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "totp_enabled": current_user.totp_enabled,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }
