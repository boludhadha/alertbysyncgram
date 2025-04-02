# bot/listener.py
import logging
from telegram import Update
from telegram.ext import CallbackContext
from utils.filters import is_signal_message
from backend import alerts

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    logger.info("Received message: %s", text)
    if is_signal_message(text):
        logger.info("Signal detected in message: %s", text)
        # Process the signal (make sure your alerts.process_signal is async or use await if needed)
        await alerts.process_signal(update)
    else:
        logger.info("Message did not contain a signal keyword.")
