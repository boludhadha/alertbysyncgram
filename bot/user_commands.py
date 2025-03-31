# bot/user_commands.py
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackContext
from db.database import SessionLocal
from models.user import User
from models.group import Group
from models.call_subscription import CallAlertSubscription

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome to SyncGram Alerts! Use /subscribe to start receiving call alerts.")

async def subscribe(update: Update, context: CallbackContext):
    await update.message.reply_text("Please send your phone number in the format +1234567890 to subscribe.")

async def handle_phone(update: Update, context: CallbackContext):
    phone_number = update.message.text.strip()
    telegram_id = str(update.message.from_user.id)
    db = SessionLocal()
    
    # Create or update user record.
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, phone_number=phone_number)
        db.add(user)
        db.commit()
    else:
        user.phone_number = phone_number
        db.commit()
    
    # Subscribe the user to the current group.
    chat_id = str(update.message.chat.id)
    group = db.query(Group).filter(Group.telegram_group_id == chat_id).first()
    if not group:
        group = Group(telegram_group_id=chat_id, name=update.message.chat.title or "Unknown")
        db.add(group)
        db.commit()
    
    subscription = db.query(CallAlertSubscription).filter(
        CallAlertSubscription.user_id == user.id,
        CallAlertSubscription.group_id == group.id
    ).first()
    
    if not subscription:
        subscription = CallAlertSubscription(user_id=user.id, group_id=group.id)
        db.add(subscription)
        db.commit()
    
    await update.message.reply_text("You have been subscribed to call alerts for this group!")
    db.close()

def register_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(MessageHandler(filters.Regex(r'^\+\d{10,15}$'), handle_phone))
