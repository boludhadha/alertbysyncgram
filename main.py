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

# Allow nested event loops
nest_asyncio.apply()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# (External DB tables are managed via ormar in models; no local DB for subscriptions here.)
from db.internal_database import engine, Base
Base.metadata.create_all(bind=engine)
logger.info("Internal database tables created.")

# Import Telegram bot handlers.
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from bot.alerts_bot import register_alerts_handlers

def start_fastapi():
    logger.info("Starting FastAPI webhook server on port 8000")
    uvicorn.run("backend.webhook:app", host="0.0.0.0", port=8000)

async def run_alerts_bot():
    token = os.getenv("ALERTS_BOT_TOKEN")
    if not token:
        logger.error("ALERTS_BOT_TOKEN is not set in the environment!")
        return
    logger.info("Initializing AlertsBySyncGram Bot with token: %s", token)
    app_alerts = ApplicationBuilder().token(token).build()
    register_alerts_handlers(app_alerts)
    logger.info("Starting AlertsBySyncGram Bot polling for updates.")
    await app_alerts.run_polling(close_loop=False)

async def main():
    await asyncio.gather(
        run_alerts_bot(),
    )

if __name__ == "__main__":
    # Start the FastAPI webhook server in a daemon thread.
    threading.Thread(target=start_fastapi, daemon=True).start()
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception("Error running AlertsBySyncGram Bot: %s", e)
