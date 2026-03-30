"""
Reset the 'sam' human account password.
Run this if you've forgotten your password.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import getpass
from app.database import SessionLocal
from app.models import User
from app.auth import hash_password

def main():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == 'sam').first()
        if not user:
            print("No 'sam' account found.")
            return

        print("Reset password for account: sam")
        while True:
            pw = getpass.getpass("New password: ")
            if len(pw) < 6:
                print("Password must be at least 6 characters.")
                continue
            confirm = getpass.getpass("Confirm password: ")
            if pw != confirm:
                print("Passwords don't match. Try again.")
                continue
            break

        user.hashed_password = hash_password(pw)
        db.commit()
        print("\nPassword updated successfully!")
        print("Restart the AI-OS server and you can log in.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
