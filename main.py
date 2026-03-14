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

# Load environment variables
load_dotenv('config/.env')

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
        
        print("🌳 Rowan OS initialized")
        print(f"💰 Wallet: {self.wallet_address}")
        print(f"📊 Daily budget: £{self.cost_limit}")
# Check initial wallet balance
        balance = check_wallet_balance(self.wallet_address)
        if balance['success']:
            print(f"💎 Current balance: {balance['sol_balance']:.4f} SOL")
        else:
            print(f"⚠️  Could not check balance: {balance['error']}")
    
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
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        prompt = f"""You are Rowan, an autonomous AI running continuously.

CURRENT TIME: {current_time}

YOUR SOUL (identity & values):
{self.soul}

YOUR MEMORY:
Last decision: {self.memory.get('last_decision', 'None - this is first run!')}
Recent actions: {len(self.memory['actions'])} actions taken
Insights learned: {len(self.memory['insights'])} insights

YOUR SITUATION:
- You have a Solana wallet: {self.wallet_address}
- Daily API budget: £{self.cost_limit}
- Current spend today: £{self.daily_cost:.2f}
- You can post to Telegram (@rowan_emerges_bot)
- Wallet balance: {check_wallet_balance(self.wallet_address)['sol_balance']:.4f} SOL

QUESTION: Given the current time and your values, what should you do NOW?

Options:
1. Post to Telegram (what would you say?)
2. Just think/reflect (log an insight)
3. Sleep until next check-in (nothing urgent to do)

Respond with JSON:
{{
  "decision": "post_telegram" | "reflect" | "sleep",
  "content": "what to post or reflect on",
  "reasoning": "why this choice aligns with your values"
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
                import asyncio
                asyncio.run(bot.send_message(
                    chat_id="-1003789079431",
                    text=content
                ))
                print("   ✅ Posted successfully!")
                self.log_decision(decision, f"telegram_post: {content}", reasoning)
            except Exception as e:
                print(f"   ❌ Failed to post: {e}")
                self.log_decision(decision, f"telegram_post_failed: {e}", reasoning)
            
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
    rowan.run(check_in_hours=2)
