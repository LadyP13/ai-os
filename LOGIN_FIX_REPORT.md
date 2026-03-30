# AI-OS Companion App Login Fix Report
**Date:** 2026-03-30
**Fixed by:** Code Claude (Build Session Day 13)

---

## What Was Broken

**Login returned HTTP 500 Internal Server Error** on every attempt.

The backend would crash before even checking the username/password.

---

## Root Cause

**Incompatible `bcrypt` version in the venv.**

- Installed: `bcrypt 5.0.0`
- Required by `passlib 1.7.4`: `bcrypt <= 4.0.1`

`bcrypt 4.2+` changed its API to raise a hard `ValueError` if a password is longer than 72 bytes. `passlib`'s internal `detect_wrap_bug()` test uses a password longer than 72 bytes — so it crashed on every `verify_password()` call, before any credentials were even checked.

**Full error:**
```
ValueError: password cannot be longer than 72 bytes, truncate manually if necessary
```

---

## Fix Applied

Downgraded `bcrypt` to the last compatible version:

```bash
cd ~/ai-os/ai-os
venv/bin/pip install "bcrypt==4.0.1"
```

Also pinned it in `requirements_app.txt` so it stays fixed:
```
bcrypt==4.0.1
```

---

## How to Restart the Running Server

The server currently running on port 8000 still has the old broken bcrypt loaded in memory.
To apply the fix, restart it:

```bash
# Find and stop the current server
kill $(lsof -ti:8000)

# Wait a moment, then restart
cd ~/ai-os/ai-os
venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

Or use:
```bash
cd ~/ai-os/ai-os
python start.py
```

---

## If You've Forgotten Your Password

A reset script has been created:

```bash
cd ~/ai-os/ai-os
venv/bin/python reset_password.py
```

It will prompt you to enter a new password for the `sam` account.

---

## How to Start the App

**Production mode (recommended):**
```bash
cd ~/ai-os/ai-os
python start.py
# Opens browser at http://localhost:8000
```

**Dev mode (frontend hot-reload):**
```bash
# Terminal 1 - Backend
cd ~/ai-os/ai-os
venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd ~/ai-os/ai-os/frontend
npm run dev
# Visit http://localhost:5173
```

---

## Testing Login Works

1. Start the server (after restart)
2. Navigate to `http://localhost:8000`
3. Enter username: `sam` and your password
4. Click Sign In
5. You should land on the AI-OS dashboard

---

## What Was Already Working

- Backend CORS configuration ✅ (`http://localhost:5173` and `http://localhost:8000` allowed)
- Vite proxy configuration ✅ (`/api` → `http://localhost:8000`)
- Database initialized ✅ (`data/aios.db` exists with `sam` and `rowan` accounts)
- Frontend built ✅ (`frontend/dist/` exists)
- Auth flow logic ✅ (JWT, password hashing, 2FA all correct)
- The **only issue** was the bcrypt version
