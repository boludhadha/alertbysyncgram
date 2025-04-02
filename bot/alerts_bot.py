# bot/alerts_bot.py
import logging
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from db.external_ormar_config import database  # External DB (SyncGram subscriptions)
from models.subscription import Subscription as SyncSubscription  # External subscription model
from db.internal_database import SessionLocal  # Internal DB (for alerts subscriptions)
from models.alert_subscription import AlertSubscription  # Internal alerts subscription model
from backend.korapay import initiate_korapay_payment  # Korapay payment integration function

logger = logging.getLogger(__name__)

async def start_alerts(update: Update, context: CallbackContext):
    """
    /start command for the AlertsBySyncGram Bot.
    Connects to the external DB and fetches the groups the user belongs to,
    then presents them as inline buttons.
    """
    user_id = str(update.effective_user.id)
    await update.message.reply_text("Welcome to AlertsBySyncGram Bot! Checking your SyncGram groups...")

    # Connect to external DB and fetch subscription records (groups the user is in)
    await database.connect()
    sync_subs = await SyncSubscription.objects.filter(user_id=user_id).all()
    await database.disconnect()

    if not sync_subs:
        await update.message.reply_text("No groups found for you. Please join a SyncGram group first.")
        return

    # Build inline buttons based on the group_id from each subscription
    keyboard = []
    for sub in sync_subs:
        # Display a friendly label; here we're showing the group_id. You may enhance this if you have a group name.
        keyboard.append([InlineKeyboardButton(f"Group {sub.group_id}", callback_data=f"subscribe:{sub.group_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select the group for which you want to subscribe to AlertsBySyncGram:", reply_markup=reply_markup)

async def button_handler(update: Update, context: CallbackContext):
    """
    Handles callback queries when the user selects a group.
    Stores the selected group id in user_data and asks for the user's phone number.
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
    Receives the phone number from the user, then creates a new AlertSubscription
    record in the internal database. After creating the record, it initiates payment via Korapay.
    """
    phone = update.message.text.strip()
    group_id = context.user_data.get("alert_group_id")
    user_id = str(update.effective_user.id)
    if not group_id:
        await update.message.reply_text("Please select a group first using /start.")
        return

    # Create a new alert subscription in the internal database.
    session = SessionLocal()
    start_date = datetime.datetime.utcnow()
    # Let's assume the subscription is valid for 30 days.
    end_date = start_date + datetime.timedelta(days=30)
    new_alert_sub = AlertSubscription(
        telegram_user_id=user_id,
        group_id=group_id,
        phone_number=phone,
        subscription_start=start_date,
        subscription_end=end_date,
        active=False  # Initially inactive until payment is confirmed.
    )
    session.add(new_alert_sub)
    session.commit()
    session.refresh(new_alert_sub)
    session.close()

    # Initiate Korapay payment and generate a payment link.
    # Replace the redirect URL with your actual payment confirmation endpoint.
    payment_link = initiate_korapay_payment(amount=1000, subscription_id=new_alert_sub.id, redirect_url="https://yourdomain.com/payment_complete")
    
    if payment_link:
        # Save the new alert subscription id for later reference (e.g., for confirming payment)
        context.user_data["alert_subscription_id"] = str(new_alert_sub.id)
        await update.message.reply_text(
            f"Please complete your payment of ₦1000 here: {payment_link}\nAfter payment, type /payment_success to confirm."
        )
    else:
        await update.message.reply_text("Error initiating payment. Please try again later.")

async def payment_success(update: Update, context: CallbackContext):
    """
    Confirms payment and marks the alert subscription as active.
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
    Registers the handlers for the AlertsBySyncGram Bot.
    """
    from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
    application.add_handler(CommandHandler("start", start_alerts))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^\+\d{10,15}$'), handle_phone_alerts))
    application.add_handler(CommandHandler("payment_success", payment_success))
