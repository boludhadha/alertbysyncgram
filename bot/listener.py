# bot/listener.py
import logging
from telegram import Update
from telegram.ext import CallbackContext
from utils.filters import is_signal_message
from backend import alerts

logger = logging.getLogger(__name__)

def handle_message(update: Update, context: CallbackContext):
    message_text = update.message.text
    if is_signal_message(message_text):
        # Process signal messages to trigger calls for subscribers.
        alerts.process_signal(update)
