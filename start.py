"""
AI-OS Launcher: starts the FastAPI server and opens the browser.
"""

import subprocess
import webbrowser
import time
import sys
import os
from pathlib import Path

# Ensure data dir exists
(Path(__file__).parent / "data").mkdir(exist_ok=True)

# Check if DB exists (i.e., setup has been run)
db_path = Path(__file__).parent / "data" / "aios.db"
if not db_path.exists():
    print("No database found. Running setup first...")
    print()
    result = subprocess.run([sys.executable, "setup.py"])
    if result.returncode != 0:
        sys.exit(1)
    print()

# Start the FastAPI server
print("Starting AI-OS server...")
server = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"],
    cwd=str(Path(__file__).parent)
)
time.sleep(2)  # wait for server to start

# Open browser
webbrowser.open("http://localhost:8000")

print("AI-OS running at http://localhost:8000")
print("Press Ctrl+C to stop")

try:
    server.wait()
except KeyboardInterrupt:
    print("\nShutting down...")
    server.terminate()
    server.wait()
    print("AI-OS stopped.")
