# main.py
import os
import threading
import asyncio
import uvicorn

# Load environment variables if using .env
from dotenv import load_dotenv
load_dotenv()

# Create database tables.
from db.database import engine, Base

# Import all models so they are registered with Base
import models.user
import models.group
import models.call_subscription
import models.call_log

# Create tables (if they don't exist)
Base.metadata.create_all(bind=engine)

# Import handlers for your Telegram bot
from bot.user_commands import start, subscribe, handle_phone
from bot.listener import handle_message
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

def start_fastapi():
    uvicorn.run("backend.webhook:app", host="0.0.0.0", port=8000)

async def main_telegram_bot():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "your_telegram_token")
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.Regex(r'^\+\d{10,15}$'), handle_phone))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    await application.run_polling()

if __name__ == "__main__":
    fastapi_thread = threading.Thread(target=start_fastapi, daemon=True)
    fastapi_thread.start()
    
    asyncio.run(main_telegram_bot())
