# bot/alerts_bot.py
import logging
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from db.external_ormar_config import database  # External DB for subscriptions
from models.subscription import Subscription  # External subscription model

logger = logging.getLogger(__name__)

async def start_alerts(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    await update.message.reply_text("Welcome to AlertsBySyncGram Bot! Checking your subscription data...")

    await database.connect()
    subs = await Subscription.objects.filter(user_id=user_id).all()
    await database.disconnect()

    if not subs:
        await update.message.reply_text("No subscriptions found for you. Please ask your SyncGram admin to add you to a group.")
        return

    keyboard = []
    for sub in subs:
        # Display a friendly label; here we show the group_id – adjust as needed.
        keyboard.append([InlineKeyboardButton(f"Group {sub.group_id}", callback_data=f"subscribe:{sub.id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select the group for which you want to receive alerts:", reply_markup=reply_markup)

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data  # Expected format: "subscribe:<subscription_id>"
    if data.startswith("subscribe:"):
        sub_id = data.split(":")[1]
        context.user_data["subscription_id"] = sub_id
        await query.edit_message_text("Please enter your phone number in E.164 format (e.g., +234XXXXXXXXXX):")

async def handle_phone_alerts(update: Update, context: CallbackContext):
    phone = update.message.text.strip()
    sub_id = context.user_data.get("subscription_id")
    if not sub_id:
        await update.message.reply_text("Please start by selecting a group using /start.")
        return

    await database.connect()
    subscription = await Subscription.objects.get(id=sub_id)
    # Save the provided phone number into the external subscription record.
    subscription.phone_number = phone  # Ensure your Subscription model includes a field for phone number if desired.
    await subscription.update()
    await database.disconnect()

    # Construct a payment link (using Korapay or your payment gateway) – this is a placeholder.
    payment_link = f"https://korapay.com/pay?amount=1000&subscription_id={sub_id}"
    await update.message.reply_text(
        f"Please complete your payment of ₦1000 here: {payment_link}\nAfter payment, type /payment_success to confirm."
    )

async def payment_success(update: Update, context: CallbackContext):
    sub_id = context.user_data.get("subscription_id")
    if not sub_id:
        await update.message.reply_text("No subscription selected. Please use /start.")
        return

    await database.connect()
    subscription = await Subscription.objects.get(id=sub_id)
    # Mark the subscription as active once payment is confirmed.
    subscription.invite_used = True
    subscription.joined_at = datetime.datetime.utcnow()
    await subscription.update()
    await database.disconnect()

    await update.message.reply_text("Payment confirmed! You are now subscribed to alerts for this group.")

def register_alerts_handlers(application):
    from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
    application.add_handler(CommandHandler("start", start_alerts))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^\+\d{10,15}$'), handle_phone_alerts))
    application.add_handler(CommandHandler("payment_success", payment_success))
