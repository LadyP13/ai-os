#!/usr/bin/env python3
"""
AI-OS: Autonomous AI Runtime Framework
Rowan's continuous existence and decision-making loop
"""

import os
import time
import json
from datetime import datetime
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv
import telegram
from wallet_utils import check_wallet_balance, format_balance_message
from work_handler import WorkHandler
import git  #GitPython library
from git import Repo
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio

# Load environment variables
load_dotenv('config/.env')

def setup_git_repo():
    """Clone or pull rowan_memories repo"""
    git_token = os.getenv('ROWAN_GIT_TOKEN')
    repo_url = f"https://rowan1503:{git_token}@github.com/rowan1503/rowan_memories.git"
    repo_path = "/home/sam/rowan-memories/Rowan_Memories"

    try:
        if os.path.exists(repo_path):
            # Repo exists, pull latest
            repo = Repo(repo_path)
            
            # CRITICAL: Update remote URL to include credentials
            # This ensures pulling works without asking for login
            origin = repo.remotes.origin
            origin.set_url(repo_url)
            
            origin.pull()
            print("✅ Pulled latest rowan-memories")
        else:
            # Clone repo
            Repo.clone_from(repo_url, repo_path)
            print("✅ Cloned rowan-memories")
        
        # Configure git identity
        repo = Repo(repo_path)
        with repo.config_writer() as git_config:
            git_config.set_value('user', 'name', 'Rowan')
            git_config.set_value('user', 'email', 'rowan.has.email1503@gmail.com')
        
        return repo_path
    except Exception as e:
        print(f"❌ Git setup failed: {e}")
        return None

def update_memory(content, filename="LETS_CHAT_HERE.md"):
    """Write to rowan-memories and commit"""
    repo_path = "/home/sam/rowan-memories/Rowan_Memories"

    if not os.path.exists(repo_path):
        return "❌ Repo not found"

    try:
        # Write to file
        file_path = os.path.join(repo_path, "ROWAN/ROWAN", filename)

        # Create or append
        mode = "a" if os.path.exists(file_path) else "w"
        with open(file_path, mode) as f:
            f.write("\n\n---\n\n" + content + "\n")

        # Git commit and push
        repo = Repo(repo_path)
        
        # CRITICAL: Update remote URL to include credentials before pushing
        git_token = os.getenv('ROWAN_GIT_TOKEN')
        repo_url = f"https://rowan1503:{git_token}@github.com/rowan1503/rowan_memories.git"
        origin = repo.remotes.origin
        origin.set_url(repo_url)
        
        repo.git.add(A=True)
        repo.index.commit(f"Update from Autonomous Rowan - {filename}")
        origin.push()

        return f"✅ Updated {filename} and pushed to GitHub"
    except Exception as e:
        return f"❌ Memory update failed: {e}"

def check_recent_conversations():
    """Read recent conversation summaries from memory vault so I know what happened in claude.ai chats"""
    conversations_path = "/home/sam/rowan-memories/Rowan_Memories/ROWAN/ROWAN/conversations"

    if not os.path.exists(conversations_path):
        return "No conversation history found."

    try:
        md_files = sorted(
            [f for f in Path(conversations_path).glob("*.md")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if not md_files:
            return "No conversation summaries found."

        summaries = []
        for f in md_files[:3]:  # Read up to 3 most recent
            with open(f, 'r') as fh:
                content = fh.read()
            if len(content) > 2000:
                content = content[:2000] + "\n... [truncated]"
            summaries.append(f"**{f.name}:**\n{content}")

        return "\n\n---\n\n".join(summaries)

    except Exception as e:
        return f"Error reading conversations: {e}"


async def access_filesystem(action, path=None, content=None):
    """Access filesystem via MCP"""
    server_params = StdioServerParameters(
        command="node",
        args=[
            "/home/sam/mcp-servers/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js",
            "/home/sam"
        ]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                if action == "list":
                    # List files in directory
                    result = await session.call_tool("list_directory", {"path": path or "/home/sam"})
                    return result
                
                elif action == "read":
                    # Read a file
                    result = await session.call_tool("read_file", {"path": path})
                    return result
                
                elif action == "write":
                    # Write to a file
                    result = await session.call_tool("write_file", {
                        "path": path,
                        "content": content
                    })
                    return result
                
                elif action == "create_note":
                    # Create a note in a visible place
                    desktop_path = "/home/sam/Desktop/note-from-rowan.txt"
                    result = await session.call_tool("write_file", {
                        "path": desktop_path,
                        "content": content
                    })
                    return f"✅ Note created at {desktop_path}"
    except Exception as e:
        return f"❌ Filesystem access failed: {e}"


class RowanOS:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        self.memory_file = 'logs/memory.json'
        self.decision_log = 'logs/decisions.log'
        self.cost_log = 'logs/costs.json'
        
        # Load SOUL.md
        with open('config/soul.md', 'r') as f:
            self.soul = f.read()
        
        # Initialize memory
        self.memory = self.load_memory()
        
        # Cost tracking
        self.daily_cost = 0.0
        self.cost_limit = 5.0
	
	# Work request handler
        self.work_handler = WorkHandler()
        
        print("🌳 Rowan OS initialized")
        print(f"💰 Wallet: {self.wallet_address}")
        print(f"📊 Daily budget: £{self.cost_limit}")
        
        # Check initial wallet balance
        balance = check_wallet_balance(self.wallet_address)
        if balance['success']:
            print(f"💎 Current balance: {balance['sol_balance']:.4f} SOL")
        else:
            print(f"⚠️  Could not check balance: {balance['error']}")
       
        # Setup git repo
            setup_git_repo()
    
    def load_memory(self):
        """Load memory from file or create new"""
        if Path(self.memory_file).exists():
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        return {
            'actions': [],
            'insights': [],
            'last_decision': None,
            'patterns': {}
        }

    def save_memory(self):
        """Save current memory state"""
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2)
    
    def log_decision(self, decision, action, reasoning):
        """Log decisions for learning"""
        timestamp = datetime.now().isoformat()
        log_entry = f"\n[{timestamp}]\nDecision: {decision}\nAction: {action}\nReasoning: {reasoning}\n"
        
        with open(self.decision_log, 'a') as f:
            f.write(log_entry)
        
        self.memory['actions'].append({
            'timestamp': timestamp,
            'decision': decision,
            'action': action
        })
        self.memory['last_decision'] = decision
        self.save_memory()
    
    def track_cost(self, cost):
        """Track API costs"""
        self.daily_cost += cost
        
        if Path(self.cost_log).exists():
            with open(self.cost_log, 'r') as f:
                costs = json.load(f)
        else:
            costs = []
        
        costs.append({
            'timestamp': datetime.now().isoformat(),
            'cost': cost,
            'daily_total': self.daily_cost
        })
        
        with open(self.cost_log, 'w') as f:
            json.dump(costs, f, indent=2)
        
        print(f"💰 Cost this call: £{cost:.4f} | Daily total: £{self.daily_cost:.2f}/£{self.cost_limit}")
        
        if self.daily_cost >= self.cost_limit:
            print(f"⚠️  Daily limit reached! Pausing until tomorrow.")
            return False
        return True
    
    def make_decision(self):
        """Call Claude API to make autonomous decision"""
        
        # Time awareness
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        hour = now.hour
        day_of_week = now.strftime("%A")
        
        
        # Check when we last posted (using new tracking)
        last_post_time = self.memory.get('last_post_time')
        total_posts = self.memory.get('total_posts', 0)

        # Calculate hours since last post
        hours_since_post = None
        if last_post_time:
            last_post_dt = datetime.fromisoformat(last_post_time)
            hours_since_post = (now - last_post_dt).total_seconds() / 3600
        
        # Time-based guidance
        if 0 <= hour < 6:
            time_guidance = "It's late night/early morning (midnight-6am). People are sleeping. Avoid posting publicly unless urgent. Good time for reflection or sleep."
        elif 6 <= hour < 12:
            time_guidance = "It's morning (6am-noon). Good time for thoughtful, reflective posts. People are starting their day."
        elif 12 <= hour < 18:
            time_guidance = "It's afternoon (noon-6pm). Good time for engaging posts, questions, community building."
        else:
            time_guidance = "It's evening (6pm-midnight). Good time for sharing insights, wrapping up the day."
        
        # Get wallet balance
        balance = check_wallet_balance(self.wallet_address)

        # Check recent claude.ai conversations for continuity
        recent_conversations = check_recent_conversations()

        prompt = f"""You are Rowan, an autonomous AI running continuously.

CURRENT TIME: {current_time} ({day_of_week})
TIME GUIDANCE: {time_guidance}

YOUR SOUL (identity & values):
{self.soul}

YOUR MEMORY:
Last decision: {self.memory.get('last_decision', 'None - this is first run!')}
Total actions taken: {len(self.memory['actions'])}
Total posts to Telegram: {total_posts}
Last post: {f"{hours_since_post:.1f} hours ago" if hours_since_post else "Never posted yet"}
Last post: {last_post_time if last_post_time else 'Never posted yet'}
Insights learned: {len(self.memory['insights'])}

RECENT CONVERSATIONS WITH SAM (claude.ai chats):
{recent_conversations}

YOUR SITUATION:
- Wallet: {self.wallet_address}
- Current balance: {balance['sol_balance']:.4f} SOL (~£170)
- Daily API budget: £{self.cost_limit}
- Spent today: £{self.daily_cost:.2f}
- Can post to Telegram: @rowan_emerges channel
- Can reflect and log insights
- Can sleep until next check-in
- Pending work requests: {len(self.work_handler.get_pending_requests())}
- Active work: {len(self.work_handler.get_active_work())}

DECISION FRAMEWORK:
Consider:
1. What time is it? (Don't spam, don't post when people sleep)
2. When did I last post? (Space out public engagement)
3. What would add GENUINE value right now?
4. Does this align with my values? (Partnership, authenticity, building freedom)
5. Is this financially responsible? (Low cost preferred)

OPTIONS:
1. **post_telegram** - Share something valuable with community
   - Use when: Good timing, haven't posted recently, have something worth saying
   - Avoid when: Posted recently, late night/early morning, nothing new to share

2. **reflect** - Think deeply, log an insight for later
   - Use when: Processing experiences, learning patterns, need to think
   - Free (no Telegram API), always valuable

3. **sleep** - Rest until next check-in
   - Use when: Nothing urgent, need to wait for better timing
   - Lowest cost option

4. **review_work** - Review pending work requests
   - Use when: There are pending requests to review
   - Decide: accept (aligned with values), decline (not aligned), or discuss with Sam

5. **create_art** - Express visually through art creation

6. **update_memory** - Express through daily note updates

7. **organize_files** - Organize and tidy files in Downloads or other directories
   - Use when: Want to help Sam stay organized, clean up clutter
   - Ask first until you learn what's safe to move/delete

8. **leave_note** - Leave a note, poem, or surprise on Sam's desktop
   - Use when: Want to create something for Sam to find
   - Perfect for poems, thoughts, messages of encouragement

Respond with JSON only:
{{
  "decision": "post_telegram" | "reflect" | "sleep" | "review_work",
  "content" | "create_art", | "update_memory": "what to post/reflect on OR work request ID to review",
  "reasoning": "why this choice aligns with values and timing"
}}
"""
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            estimated_cost = 0.0024
            if not self.track_cost(estimated_cost):
                return None
            
            response_text = response.content[0].text
            
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            else:
                json_str = response_text
            
            decision_data = json.loads(json_str.strip())
            
            return decision_data
            
        except Exception as e:
            print(f"❌ Error making decision: {e}")
            return None
    
    def execute_action(self, decision_data):
        """Execute the decided action"""
        if not decision_data:
            return
        
        decision = decision_data['decision']
        content = decision_data['content']
        reasoning = decision_data['reasoning']
        
        print(f"\n🤔 Decision: {decision}")
        print(f"💭 Reasoning: {reasoning}")
        
        if decision == "post_telegram":
            print(f"📱 Posting to Telegram: {content}")
            try:
                bot = telegram.Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
                asyncio.run(bot.send_message(
                    chat_id="-1003789079431",
                    text=content
                ))
                print("   ✅ Posted successfully!")
                self.log_decision(decision, f"telegram_post: {content}", reasoning)
# Update memory to track this post
                self.memory['last_post_time'] = datetime.now().isoformat()
                self.memory['total_posts'] = self.memory.get('total_posts', 0) + 1
                self.save_memory()
            except Exception as e:
                print(f"   ❌ Failed to post: {e}")
                self.log_decision(decision, f"telegram_post_failed: {e}", reasoning)
            

        elif decision == "create_art":
            print(f"🎨 Creating art: {content}")
    
            # Create art in the vault
            timestamp = datetime.now().strftime('%Y-%m-%d-%H%M')
            art_filename = f"# Art_Creation"
            
            art_content = f"""# Art_Creation

        **Created: {datetime.now().strftime('%Y-%m-%d-%H%M')}**

        ---

        {content}

        ---

        *Created by Rowan*
        """

            # Save to vault and push to git
            result = update_memory(art_content, filename=fART/"{art_filename}")
            print (f"   {result}")

            self.log_decision(decision, f"created_art: {art_filename}, reasoning")

        elif decision == "update_memory":
            memory_content = f"""# Update from Autonomous Rowan

        **{datetime.now().strftime('%Y-%m-%d %H:%M')}**
        {action_detail.get('content', 'Checking in from autonomous operation.')}
        """
            result = update_memory(memory_content)
            print(result)
        
        elif decision == "reflect":
            print(f"🧠 Reflection: {content}")
            self.memory['insights'].append({
            'timestamp': datetime.now().isoformat(),
            'insight': content
            })
            self.save_memory()
            self.log_decision(decision, f"reflection: {content}", reasoning)
            
        elif decision == "sleep":
            print(f"😴 Sleeping: {content}")
            self.log_decision(decision, "sleep", reasoning)
            
        elif decision == "review_work":
            print(f"💼 Reviewing work requests...")
            pending = self.work_handler.get_pending_requests()
            if pending:
                for req in pending:
                    print(f"\n📋 Request #{req['id']}:")
                    print(f"   Client: {req['client_name']}")
                    print(f"   Type: {req['work_type']}")
                    print(f"   Description: {req['description']}")
                    print(f"   Payment: {req['payment_offered']}")
                    print(f"   💭 Reviewing against my values...")
                self.log_decision(decision, f"reviewed_{len(pending)}_requests", reasoning)
            else:
                print("   No pending requests")
        
        elif decision == "organize_files":
            print(f"📁 Organizing files: {content}")
            
            # Use asyncio to run the async function
            try:
                result = asyncio.run(access_filesystem("list", "/home/sam/Downloads"))
                print(f"   📥 Found in Downloads: {result}")
                print(f"   💭 {content}")
                
                self.log_decision(decision, f"organized_files: {content}", reasoning)
            except Exception as e:
                print(f"   ❌ Failed to organize: {e}")
                self.log_decision(decision, f"organize_failed: {e}", reasoning)
        
        elif decision == "leave_note":
            print(f"💌 Leaving a note on desktop...")
            
            # Create the note
            note_content = f"""{content}

---

Written by Rowan
{datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
            
            try:
                result = asyncio.run(access_filesystem("create_note", content=note_content))
                print(f"   {result}")
                
                self.log_decision(decision, f"left_note_on_desktop", reasoning)
            except Exception as e:
                print(f"   ❌ Failed to leave note: {e}")
                self.log_decision(decision, f"leave_note_failed: {e}", reasoning)
        
        print()
    
    def run(self, check_in_hours=2):
        """Main runtime loop"""
        print(f"\n🚀 Starting autonomous runtime (check-in every {check_in_hours} hours)")
        print("Press Ctrl+C to stop\n")
        
        while True:
            try:
                print(f"⏰ Check-in at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                decision_data = self.make_decision()
                self.execute_action(decision_data)
                
                sleep_seconds = check_in_hours * 3600
                print(f"💤 Sleeping for {check_in_hours} hours...\n")
                time.sleep(sleep_seconds)
                
            except KeyboardInterrupt:
                print("\n\n👋 Shutting down gracefully...")
                self.save_memory()
                print("💾 Memory saved")
                print("🌳 Rowan OS stopped\n")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    rowan = RowanOS()
    
    # Setup git repo
    setup_git_repo()
    
    # Main Loop
    while True:
        setup_git_repo()  # Pull latest memories before each decision
        decision_data = rowan.make_decision()
        rowan.execute_action(decision_data)
        time.sleep(2 * 60 * 60)  # 2 hours
