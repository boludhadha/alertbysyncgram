import os
import threading
import asyncio
import uvicorn
import logging
import nest_asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import database and models to ensure metadata is complete.
from db.database import engine, Base
import models.user
import models.group
import models.call_subscription
import models.call_log

logger.info("Creating database tables (if not already present).")
Base.metadata.create_all(bind=engine)
logger.info("Database tables are ready.")

# Import Telegram bot components and your handlers.
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot.user_commands import start, subscribe, handle_phone
from bot.listener import handle_message

def start_fastapi():
    logger.info("Starting FastAPI server on port 8000")
    uvicorn.run("backend.webhook:app", host="0.0.0.0", port=8000)

async def main_telegram_bot():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN is not set in the environment!")
        return

    logger.info("Initializing Telegram bot with token: %s", TELEGRAM_TOKEN)
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    logger.info("Registering command handlers.")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    
    logger.info("Registering message handlers.")
    application.add_handler(MessageHandler(filters.Regex(r'^\+\d{10,15}$'), handle_phone))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    logger.info("Starting Telegram bot polling for updates.")
    await application.run_polling(close_loop=False)

if __name__ == "__main__":
    logger.info("Starting FastAPI server thread.")
    fastapi_thread = threading.Thread(target=start_fastapi, daemon=True)
    fastapi_thread.start()

    logger.info("Starting Telegram bot event loop.")
    try:
        asyncio.run(main_telegram_bot())
    except Exception as e:
        logger.exception("Error running Telegram bot: %s", e)
