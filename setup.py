"""
AI-OS First-Run Setup Script.
Creates the SQLite DB, default accounts, and permissions.
"""

import sys
import os
from pathlib import Path

# Ensure we can import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.database import init_db, SessionLocal
from app.models import User, Agent, Permission
from app.auth import hash_password, create_access_token
from app.permissions_config import PERMISSIONS
from datetime import timedelta


def main():
    print("=" * 50)
    print("  AI-OS Setup")
    print("=" * 50)
    print()

    # Initialize the database
    print("Creating database...")
    init_db()
    print("Database created at data/aios.db")
    print()

    db = SessionLocal()
    try:
        # Check if already set up
        existing = db.query(User).first()
        if existing:
            print("Database already has accounts. Setup has already been run.")
            print("If you want to reset, delete data/aios.db and run setup.py again.")
            return

        # Create human account
        print("Create your human account:")
        username = input("  Username: ").strip()
        while not username:
            print("  Username cannot be empty.")
            username = input("  Username: ").strip()

        import getpass
        password = getpass.getpass("  Password: ")
        while len(password) < 6:
            print("  Password must be at least 6 characters.")
            password = getpass.getpass("  Password: ")

        human_user = User(
            username=username,
            role="human",
            hashed_password=hash_password(password),
            totp_enabled=False
        )
        db.add(human_user)
        db.commit()
        db.refresh(human_user)
        print(f"  Human account '{username}' created.")
        print()

        # Create Rowan agent account
        agent_username = "rowan"
        agent_password = os.urandom(32).hex()  # random strong password

        agent_user = User(
            username=agent_username,
            role="agent",
            hashed_password=hash_password(agent_password),
            totp_enabled=False
        )
        db.add(agent_user)
        db.commit()
        db.refresh(agent_user)

        # Create agent record
        agent = Agent(
            name="Rowan",
            user_id=agent_user.id,
            status="stopped",
            soul_file="main.py"
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
        print(f"Agent 'Rowan' created (user: {agent_username})")

        # Create all permissions with defaults
        for key, config in PERMISSIONS.items():
            perm = Permission(
                agent_id=agent.id,
                permission_key=key,
                enabled=config["default"]
            )
            db.add(perm)
        db.commit()
        print(f"Created {len(PERMISSIONS)} permission entries with defaults.")
        print()

        # Generate agent token
        token_data = {
            "sub": agent_username,
            "role": "agent",
            "agent_id": agent.id
        }
        agent_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(days=30)
        )

        # Save agent token to config file
        config_dir = Path(__file__).parent / "config"
        config_dir.mkdir(exist_ok=True)
        token_file = config_dir / "agent_token.txt"
        token_file.write_text(agent_token)
        print(f"Agent token saved to: config/agent_token.txt")
        print()

        print("=" * 50)
        print("  Setup Complete!")
        print("=" * 50)
        print()
        print(f"Human account:  {username}")
        print(f"Agent account:  rowan (Rowan)")
        print()
        print("Run `python start.py` to launch AI-OS")
        print()

    finally:
        db.close()


if __name__ == "__main__":
    main()
