# bot/user_commands.py
from telegram import Update
from telegram.ext import CallbackContext
from db.internal_database import SessionLocal
from models.user import User
from models.group import Group
from models.call_subscription import CallAlertSubscription
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    logger.info("Received /start command from user: %s", update.effective_user.id)
    await update.message.reply_text("Welcome to AlertsBySyncGram! Use /subscribe to start receiving call alerts.")

async def subscribe(update: Update, context: CallbackContext):
    logger.info("Received /subscribe command from user: %s", update.effective_user.id)
    await update.message.reply_text("Please send your phone number in the format +1234567890 to subscribe.")

async def handle_phone(update: Update, context: CallbackContext):
    phone_number = update.message.text.strip()
    telegram_id = str(update.message.from_user.id)
    logger.info("Received phone number %s from user: %s", phone_number, telegram_id)
    
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        logger.info("User %s not found, creating new record.", telegram_id)
        user = User(telegram_id=telegram_id, phone_number=phone_number)
        db.add(user)
        db.commit()
    else:
        logger.info("User %s found, updating phone number.", telegram_id)
        user.phone_number = phone_number
        db.commit()
    
    chat_id = str(update.message.chat.id)
    group = db.query(Group).filter(Group.telegram_group_id == chat_id).first()
    if not group:
        logger.info("Group %s not found, creating new group record.", chat_id)
        group = Group(telegram_group_id=chat_id, name=update.message.chat.title or "Unknown")
        db.add(group)
        db.commit()
    
    subscription = db.query(CallAlertSubscription).filter(
        CallAlertSubscription.user_id == user.id,
        CallAlertSubscription.group_id == group.id
    ).first()
    
    if not subscription:
        logger.info("No subscription for user %s in group %s, creating one.", telegram_id, chat_id)
        subscription = CallAlertSubscription(user_id=user.id, group_id=group.id)
        db.add(subscription)
        db.commit()
    else:
        logger.info("User %s already subscribed to group %s", telegram_id, chat_id)
    
    await update.message.reply_text("You have been subscribed to call alerts for this group!")
    db.close()
