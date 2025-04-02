# bot/alerts_bot.py
import logging
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from db.external_ormar_config import database  # External DB for SyncGram subscriptions
from models.subscription import Subscription as SyncSubscription  # External subscription model
from db.internal_database import SessionLocal  # Internal DB for alerts subscriptions
from models.alert_subscription import AlertSubscription  # Internal alerts subscription model
from backend.korapay import initiate_korapay_payment  # Korapay payment integration

logger = logging.getLogger(__name__)

async def start_alerts(update: Update, context: CallbackContext):
    """
    /start command for the AlertsBySyncGram Bot.
    Connects to the external DB and fetches the groups the user is in.
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

    # Build inline buttons based on the group_id from each subscription.
    keyboard = []
    for sub in sync_subs:
        keyboard.append([InlineKeyboardButton(f"Group {sub.group_id}", callback_data=f"subscribe:{sub.group_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select the group for which you want to subscribe to AlertsBySyncGram:", reply_markup=reply_markup)

async def button_handler(update: Update, context: CallbackContext):
    """
    Handles button callbacks when the user selects a group.
    Stores the selected group id and prompts for the phone number.
    """
    query = update.callback_query
    await query.answer()
    data = query.data  # Expected format "subscribe:<group_id>"
    if data.startswith("subscribe:"):
        group_id = data.split(":", 1)[1]
        context.user_data["alert_group_id"] = group_id
        await query.edit_message_text("Please enter your phone number in E.164 format (e.g., +234XXXXXXXXXX):")

async def handle_phone_alerts(update: Update, context: CallbackContext):
    """
    Collects the phone number from the user and then prompts for their email address.
    """
    phone = update.message.text.strip()
    # Save the phone number for later use.
    context.user_data["phone"] = phone
    await update.message.reply_text("Thank you. Now please enter your email address (e.g., user@example.com):")

async def handle_email_alerts(update: Update, context: CallbackContext):
    """
    Collects the email address from the user, then creates a new alert subscription in the internal DB,
    and finally initiates payment via Korapay.
    """
    email = update.message.text.strip()
    context.user_data["email"] = email

    group_id = context.user_data.get("alert_group_id")
    user_id = str(update.effective_user.id)
    if not group_id:
        await update.message.reply_text("Please select a group first using /start.")
        return

    # Create a new alert subscription record in the internal database.
    session = SessionLocal()
    start_date = datetime.datetime.utcnow()
    # For example, the subscription is valid for 30 days.
    end_date = start_date + datetime.timedelta(days=30)
    new_alert_sub = AlertSubscription(
        telegram_user_id=user_id,
        group_id=group_id,
        phone_number=context.user_data.get("phone"),
        subscription_start=start_date,
        subscription_end=end_date,
        active=False  # Initially inactive until payment is confirmed.
    )
    session.add(new_alert_sub)
    session.commit()
    session.refresh(new_alert_sub)
    session.close()

    # Initiate Korapay payment.
    # Replace "https://yourdomain.com/payment_complete" with your actual redirect URL.
    payment_link = initiate_korapay_payment(
        amount=1000,
        subscription_id=new_alert_sub.id,
        redirect_url="https://yourdomain.com/payment_complete",
        customer_email=email,
        customer_name=""  # You can also ask for and use the customer's name if desired.
    )
    
    if payment_link:
        # Store the new subscription's ID for later confirmation.
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
    Registers all handlers for the AlertsBySyncGram Bot.
    """
    from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
    application.add_handler(CommandHandler("start", start_alerts))
    application.add_handler(CallbackQueryHandler(button_handler))
    # Use a regex for phone numbers.
    application.add_handler(MessageHandler(filters.Regex(r'^\+\d{10,15}$'), handle_phone_alerts))
    # Use a simple regex for email addresses (this is a basic pattern; adjust as needed).
    application.add_handler(MessageHandler(filters.Regex(r'^[\w\.-]+@[\w\.-]+\.\w+$'), handle_email_alerts))
    application.add_handler(CommandHandler("payment_success", payment_success))
