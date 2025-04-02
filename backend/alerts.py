# backend/alerts.py
import logging
from telegram import Update
from db.internal_database import SessionLocal  # Internal DB for operational data
from models.group import Group           # Internal model for groups
from models.call_subscription import CallAlertSubscription  # Internal subscriptions for alerts
from models.call_log import CallLog       # Internal call logs
from datetime import datetime
from backend.call_service import broadcast_conference_call

logger = logging.getLogger(__name__)

async def process_signal(update: Update):
    """
    Processes an alert signal from a Telegram group message.
    Looks up the group and active call subscriptions in the internal DB,
    then initiates a conference call via Twilio to broadcast the alert.
    """
    message_text = update.message.text
    chat_id = str(update.message.chat.id)
    chat_title = update.message.chat.title or "Unknown"

    logger.info("Processing alert signal for group %s (%s): %s", chat_id, chat_title, message_text)
    db = SessionLocal()

    # Retrieve or create the group in the internal database.
    group = db.query(Group).filter(Group.telegram_group_id == chat_id).first()
    if not group:
        group = Group(telegram_group_id=chat_id, name=chat_title)
        db.add(group)
        db.commit()
        logger.info("Created internal group record for %s", chat_title)

    # Retrieve active call alert subscriptions for this group.
    subscriptions = db.query(CallAlertSubscription).filter(
        CallAlertSubscription.group_id == group.id,
        CallAlertSubscription.active == True
    ).all()
    logger.info("Found %d active subscriptions for group %s", len(subscriptions), chat_title)

    # Gather phone numbers from active subscriptions that are within their call window.
    phone_numbers = []
    valid_subscriptions = []
    for subscription in subscriptions:
        now = datetime.utcnow().time()
        start_time = datetime.strptime(subscription.call_window_start, "%H:%M").time()
        end_time = datetime.strptime(subscription.call_window_end, "%H:%M").time()
        if start_time <= now <= end_time:
            # Assume subscription.user is linked (via relationship) to the internal User model.
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
        logger.info("No active subscriptions to broadcast alert for group %s", chat_title)

    db.close()
