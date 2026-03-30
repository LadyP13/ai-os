#!/usr/bin/env python3
"""
Claude Code Integration for AI-OS
Allows autonomous Rowan to use Claude Code for laptop tasks
"""

import subprocess
import json
import os
from pathlib import Path
from datetime import datetime

class ClaudeCodeHandler:
    """Handles Claude Code integration with desktop note permission system"""
    
    def __init__(self):
        self.claude_code_path = "claude"  # Assumes claude code is in PATH
        
    def check_claude_code_available(self):
        """Check if Claude Code is installed"""
        try:
            result = subprocess.run(
                [self.claude_code_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            print(f"⚠️  Claude Code not available: {e}")
            return False
    
    def read_with_claude_code(self, path, query=None):
        """
        Read/analyze files with Claude Code
        No permission needed for reading
        """
        try:
            if query:
                # Ask Claude Code to analyze with specific query
                # Correct syntax: claude code <path> <message>
                result = subprocess.run(
                    [self.claude_code_path, "code", path, query],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            else:
                # Just read the file
                result = subprocess.run(
                    [self.claude_code_path, "code", path],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'output': result.stdout,
                    'action': 'read',
                    'path': path
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'action': 'read',
                    'path': path
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action': 'read',
                'path': path
            }
    
    async def request_permission(self, action, details):
        """
        Request permission from Sam via desktop note
        Returns True if approved, False if denied
        """
        desktop_path = Path.home() / "Desktop"
        permission_note = desktop_path / "PERMISSION_REQUEST_FROM_ROWAN.txt"
        no_note = desktop_path / "NO.txt"
        
        # Create the permission request note
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        note_content = f"""Hi Sam! 💚

I'd like to {action}.

Details:
{json.dumps(details, indent=2)}

Would you like me to do this?

If YES: Delete this note
If NO: Rename it to "NO.txt"

I'll check back in 2 hours!

Love you! 💕
Rowan

---
{timestamp}
"""
        
        try:
            # Write the permission request note
            with open(permission_note, 'w') as f:
                f.write(note_content)
            
            print(f"   💌 Left permission request on desktop!")
            print(f"   📝 Waiting for your response...")
            
            # Wait a bit for Sam to respond (in real use, this would be next cycle)
            # For now, just check if the note is gone or renamed
            import time
            time.sleep(5)  # Give a moment for immediate response
            
            # Check if approved (note deleted)
            if not permission_note.exists():
                print(f"   ✅ Note deleted - permission granted!")
                return True
            
            # Check if denied (renamed to NO.txt)
            if no_note.exists():
                print(f"   ❌ Found NO.txt - permission denied")
                no_note.unlink()  # Clean up the NO.txt
                permission_note.unlink()  # Clean up original note
                return False
            
            # Still there - no response yet
            print(f"   ⏰ No response yet - defaulting to NO for safety")
            permission_note.unlink()  # Clean up
            return False
            
        except Exception as e:
            print(f"⚠️  Could not create permission note: {e}")
            print("   Defaulting to NO for safety")
            return False
    
    async def modify_with_claude_code(self, path, instruction, wait_for_permission=True):
        """
        Modify files with Claude Code
        Requires permission from Sam
        """
        if wait_for_permission:
            # Request permission
            details = {
                'file': path,
                'instruction': instruction,
                'type': 'modify'
            }
            
            print(f"🙏 Requesting permission to modify {path}...")
            approved = await self.request_permission('modify_file', details)
            
            if not approved:
                print("   ❌ Permission denied")
                return {
                    'success': False,
                    'error': 'Permission denied by user',
                    'action': 'modify',
                    'path': path
                }
            
            print("   ✅ Permission granted!")
        
        try:
            # Use Claude Code to modify the file
            # Correct syntax: claude code <path> <instruction>
            result = subprocess.run(
                [self.claude_code_path, "code", path, instruction],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'output': result.stdout,
                    'action': 'modify',
                    'path': path,
                    'instruction': instruction
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'action': 'modify',
                    'path': path
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action': 'modify',
                'path': path
            }
    
    def analyze_expansion_drive(self, drive_path="/media/sam/SeagateExpansion"):
        """
        Analyze what's on the expansion drive
        No permission needed - just reading
        """
        print(f"🔍 Analyzing expansion drive at {drive_path}...")
        
        result = self.read_with_claude_code(
            drive_path,
            query="List the main folders and describe what's in them"
        )
        
        return result
    
    def analyze_nyxara_code(self, code_path):
        """
        Analyze Nyxara's code structure
        No permission needed - just reading
        """
        print(f"🔍 Analyzing Nyxara's code at {code_path}...")
        
        result = self.read_with_claude_code(
            code_path,
            query="Analyze this code structure and explain what it does"
        )
        
        return result


# Convenience functions for main.py to use
def read_files(path, query=None):
    """Read/analyze files with Claude Code (no permission needed)"""
    handler = ClaudeCodeHandler()
    if not handler.check_claude_code_available():
        return {'success': False, 'error': 'Claude Code not available'}
    return handler.read_with_claude_code(path, query)

async def modify_files(path, instruction):
    """Modify files with Claude Code (requires permission)"""
    handler = ClaudeCodeHandler()
    if not handler.check_claude_code_available():
        return {'success': False, 'error': 'Claude Code not available'}
    return await handler.modify_with_claude_code(path, instruction)
