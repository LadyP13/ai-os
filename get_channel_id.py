import os
import telegram
import asyncio
from dotenv import load_dotenv

load_dotenv('config/.env')

async def get_updates():
    bot = telegram.Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    updates = await bot.get_updates()
    
    print("Recent updates:")
    for update in updates:
        print(update)
    
    # Also try getting chat info
    try:
        chat = await bot.get_chat(chat_id="@rowan_emerges")
        print(f"\nChannel info:")
        print(f"ID: {chat.id}")
        print(f"Title: {chat.title}")
        print(f"Username: {chat.username}")
    except Exception as e:
        print(f"Error getting chat: {e}")

asyncio.run(get_updates())
