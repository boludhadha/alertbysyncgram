# bot/alerts_bot.py
import logging
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from db.external_ormar_config import database  # External DB for SyncGram subscriptions
from models.subscription import Subscription as SyncSubscription  # External subscription model
from db.internal_database import SessionLocal  # Internal DB for AlertsBySyncGram
from models.alert_subscription import AlertSubscription  # Internal alerts subscription model
from backend.korapay import initiate_korapay_payment  # Korapay integration

logger = logging.getLogger(__name__)

async def start_alerts(update: Update, context: CallbackContext):
    """
    /start command for AlertsBySyncGram Bot.
    Fetches groups from the external SyncGram subscriptions DB that the user belongs to.
    """
    user_id = str(update.effective_user.id)
    await update.message.reply_text("Welcome to AlertsBySyncGram Bot! Checking your SyncGram groups...")
    
    # Connect to external DB and fetch subscriptions for this user.
    await database.connect()
    sync_subs = await SyncSubscription.objects.filter(user_id=user_id).all()
    await database.disconnect()

    if not sync_subs:
        await update.message.reply_text("No groups found for you. Please join a SyncGram group first.")
        return

    # Create buttons for each group (displaying group_id; enhance as needed)
    keyboard = []
    for sub in sync_subs:
        keyboard.append([InlineKeyboardButton(f"Group {sub.group_id}", callback_data=f"subscribe:{sub.group_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select the group for which you want to subscribe to AlertsBySyncGram:", reply_markup=reply_markup)

async def button_handler(update: Update, context: CallbackContext):
    """
    Handles the button callback when a user selects a group.
    Stores the selected group id and prompts for the phone number.
    """
    query = update.callback_query
    await query.answer()
    data = query.data  # Expected format: "subscribe:<group_id>"
    if data.startswith("subscribe:"):
        group_id = data.split(":", 1)[1]
        context.user_data["alert_group_id"] = group_id
        await query.edit_message_text("Please enter your phone number in E.164 format (e.g., +234XXXXXXXXXX):")

async def handle_phone_alerts(update: Update, context: CallbackContext):
    """
    Once the user provides their phone number, create a new alert subscription
    record in the internal DB and then initiate payment via Korapay.
    """
    phone = update.message.text.strip()
    group_id = context.user_data.get("alert_group_id")
    user_id = str(update.effective_user.id)
    if not group_id:
        await update.message.reply_text("Please select a group first using /start.")
        return

    # Create a new alert subscription record in the internal DB.
    session = SessionLocal()
    start_date = datetime.datetime.utcnow()
    # For example, subscription valid for 30 days.
    end_date = start_date + datetime.timedelta(days=30)
    new_alert_sub = AlertSubscription(
        telegram_user_id=user_id,
        group_id=group_id,
        phone_number=phone,
        subscription_start=start_date,
        subscription_end=end_date,
        active=False  # Inactive until payment confirmation.
    )
    session.add(new_alert_sub)
    session.commit()
    session.refresh(new_alert_sub)
    session.close()

    # Initiate Korapay payment.
    # Replace the redirect URL with your actual endpoint for payment confirmation.
    payment_link = initiate_korapay_payment(amount=1000, subscription_id=new_alert_sub.id, redirect_url="https://yourdomain.com/payment_complete")
    
    if payment_link:
        # Store the new subscription's ID (as a string) in context for later reference.
        context.user_data["alert_subscription_id"] = str(new_alert_sub.id)
        await update.message.reply_text(
            f"Please complete your payment of ₦1000 here: {payment_link}\nAfter payment, type /payment_success to confirm."
        )
    else:
        await update.message.reply_text("Error initiating payment. Please try again later.")

async def payment_success(update: Update, context: CallbackContext):
    """
    When the user confirms payment (via /payment_success), mark the alert subscription as active.
    """
    sub_id_str = context.user_data.get("alert_subscription_id")
    if not sub_id_str:
        await update.message.reply_text("No alert subscription found. Please start with /start.")
        return
    try:
        sub_id = int(sub_id_str)
    except ValueError:
        await update.message.reply_text("Invalid subscription ID.")
        return

    session = SessionLocal()
    alert_sub = session.query(AlertSubscription).filter(AlertSubscription.id == sub_id).first()
    if alert_sub:
        alert_sub.active = True
        alert_sub.subscription_start = datetime.datetime.utcnow()
        alert_sub.subscription_end = alert_sub.subscription_start + datetime.timedelta(days=30)
        session.commit()
        await update.message.reply_text("Payment confirmed! You are now subscribed to AlertsBySyncGram for this group.")
    else:
        await update.message.reply_text("Alert subscription not found.")
    session.close()

def register_alerts_handlers(application):
    """
    Registers the command and message handlers for AlertsBySyncGram Bot.
    """
    from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
    application.add_handler(CommandHandler("start", start_alerts))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^\+\d{10,15}$'), handle_phone_alerts))
    application.add_handler(CommandHandler("payment_success", payment_success))
