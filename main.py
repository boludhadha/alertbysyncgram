# main.py
import os
import threading
import asyncio
import uvicorn
import logging
import nest_asyncio

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Apply nest_asyncio to allow nested event loops (avoid "event loop already running" error)
nest_asyncio.apply()

# Import database and model definitions
from db.database import engine, Base
import models.user
import models.group
import models.call_subscription
import models.call_log

logger.info("Creating database tables (if not already present).")
Base.metadata.create_all(bind=engine)
logger.info("Database tables are ready.")

# Import Telegram bot handlers and components
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot.user_commands import start, subscribe, handle_phone
from bot.listener import handle_message

def start_fastapi():
    """Starts the FastAPI server."""
    logger.info("Starting FastAPI server on port 8000")
    uvicorn.run("backend.webhook:app", host="0.0.0.0", port=8000)

async def main_telegram_bot():
    """Initializes and runs the Telegram bot polling."""
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "your_telegram_token")
    if TELEGRAM_TOKEN == "your_telegram_token":
        logger.error("TELEGRAM_TOKEN is not set. Please configure it in your environment.")
        return

    logger.info("Initializing Telegram bot with token: %s", TELEGRAM_TOKEN)
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Register command and message handlers
    logger.info("Registering Telegram command and message handlers.")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(MessageHandler(filters.Regex(r'^\+\d{10,15}$'), handle_phone))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    logger.info("Starting Telegram bot polling for updates.")
    await application.run_polling()

if __name__ == "__main__":
    # Start FastAPI server in a separate daemon thread
    logger.info("Starting FastAPI server thread.")
    fastapi_thread = threading.Thread(target=start_fastapi, daemon=True)
    fastapi_thread.start()

    # Run the Telegram bot polling loop in the main asyncio event loop
    logger.info("Starting Telegram bot event loop.")
    try:
        asyncio.run(main_telegram_bot())
    except Exception as e:
        logger.exception("Error running Telegram bot: %s", e)
