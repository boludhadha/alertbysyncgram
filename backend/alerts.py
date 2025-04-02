# backend/alerts.py
import logging
from telegram import Update
from db.internal_database import SessionLocal  # Internal DB for operational data
from models.group import Group            # Internal group model
from models.call_subscription import CallAlertSubscription  # Internal alert subscriptions
from models.call_log import CallLog        # Internal call logs
from datetime import datetime
from backend.call_service import broadcast_conference_call

logger = logging.getLogger(__name__)

async def process_signal(update: Update):
    """
    Processes an alert signal (e.g., a message in a group) by looking up the group
    and active alert subscriptions (from the internal DB) and initiating a conference call.
    """
    message_text = update.message.text
    chat_id = str(update.message.chat.id)
    chat_title = update.message.chat.title or "Unknown"

    logger.info("Processing alert signal for group %s (%s): %s", chat_id, chat_title, message_text)
    db = SessionLocal()

    # Retrieve or create the internal group record.
    group = db.query(Group).filter(Group.telegram_group_id == chat_id).first()
    if not group:
        group = Group(telegram_group_id=chat_id, name=chat_title)
        db.add(group)
        db.commit()
        logger.info("Created internal group record for %s", chat_title)

    # Fetch active alert subscriptions for the group.
    subscriptions = db.query(CallAlertSubscription).filter(
        CallAlertSubscription.group_id == group.id,
        CallAlertSubscription.active == True
    ).all()
    logger.info("Found %d active alert subscriptions for group %s", len(subscriptions), chat_title)

    # Collect phone numbers from subscriptions that are within the allowed call window.
    phone_numbers = []
    valid_subscriptions = []
    for subscription in subscriptions:
        now = datetime.utcnow().time()
        start_time = datetime.strptime(subscription.call_window_start, "%H:%M").time()
        end_time = datetime.strptime(subscription.call_window_end, "%H:%M").time()
        if start_time <= now <= end_time:
            # Assume subscription.user is set up via relationship, or adjust to directly use phone_number.
            phone_numbers.append(subscription.user.phone_number)
            valid_subscriptions.append(subscription)
        else:
            logger.info("Subscription ID %s is outside its call window.", subscription.id)

    if phone_numbers:
        call_message = f"New signal from {group.name}: {message_text}"
        # Initiate the conference call broadcast.
        call_sids = broadcast_conference_call(phone_numbers, conference_room=group.name, wait_url=None, message=call_message)
        for subscription in valid_subscriptions:
            number = subscription.user.phone_number
            call_sid = call_sids.get(number)
            logger.info("Conference call initiated for %s with SID: %s", number, call_sid)
            call_log = CallLog(subscription_id=subscription.id, status="initiated", details=call_sid or "failed")
            db.add(call_log)
            db.commit()
    else:
        logger.info("No active alert subscriptions for group %s", chat_title)

    db.close()
