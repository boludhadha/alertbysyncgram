import logging
from telegram import Update
from db.database import SessionLocal
from models.group import Group
from models.call_subscription import CallAlertSubscription
from models.call_log import CallLog
from datetime import datetime

logger = logging.getLogger(__name__)

from backend.call_service import broadcast_conference_call

async def process_signal(update: Update):
    """
    Processes an incoming signal from Telegram.
    Retrieves the group and active subscriptions, then broadcasts a conference call
    to all valid phone numbers.
    """
    message_text = update.message.text
    chat_id = str(update.message.chat.id)
    chat_title = update.message.chat.title or "Unknown"
    
    logger.info("Processing signal from group %s (%s) with message: %s", chat_id, chat_title, message_text)
    
    db = SessionLocal()
    # Retrieve or create the group record.
    group = db.query(Group).filter(Group.telegram_group_id == chat_id).first()
    if not group:
        group = Group(telegram_group_id=chat_id, name=chat_title)
        db.add(group)
        db.commit()
        logger.info("Created new group record: %s", chat_title)
    
    # Fetch active subscriptions for the group.
    subscriptions = db.query(CallAlertSubscription).filter(
        CallAlertSubscription.group_id == group.id,
        CallAlertSubscription.active == True
    ).all()
    
    logger.info("Found %d active subscriptions for group %s", len(subscriptions), chat_title)
    
    # Gather phone numbers that are within the valid call window.
    phone_numbers = []
    valid_subscriptions = []
    for subscription in subscriptions:
        now = datetime.utcnow().time()
        start_time = datetime.strptime(subscription.call_window_start, "%H:%M").time()
        end_time = datetime.strptime(subscription.call_window_end, "%H:%M").time()
        if start_time <= now <= end_time:
            phone_numbers.append(subscription.user.phone_number)
            valid_subscriptions.append(subscription)
        else:
            logger.info("Current UTC time is outside the call window for subscription ID %s", subscription.id)
    
    if phone_numbers:
        call_message = f"New signal from {group.name}: {message_text}"
        # Initiate the broadcast to join all recipients to the same conference.
        call_sids = broadcast_conference_call(phone_numbers, conference_room=group.name, wait_url=None, message=call_message)
        for subscription in valid_subscriptions:
            number = subscription.user.phone_number
            call_sid = call_sids.get(number)
            logger.info("Broadcast initiated call to %s with SID: %s", number, call_sid)
            call_log = CallLog(subscription_id=subscription.id, status="initiated", details=call_sid or "failed")
            db.add(call_log)
            db.commit()
    else:
        logger.info("No valid subscriptions to broadcast message.")
    
    db.close()
