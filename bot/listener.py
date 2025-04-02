# bot/listener.py
import logging
from telegram import Update
from telegram.ext import CallbackContext
from utils.filters import is_signal_message
from bot import alerts_bot

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    logger.info("Received message in group: %s", text)
    if is_signal_message(text):
        logger.info("Signal detected in message: %s", text)
        await alerts_bot.process_signal(update)
    else:
        logger.info("No signal keyword found in message.")
