import logging
from telegram import Update
from db.database import SessionLocal
from models.group import Group
from models.call_subscription import CallAlertSubscription
from models.call_log import CallLog
from backend.call_service import initiate_call
from datetime import datetime

logger = logging.getLogger(__name__)

async def process_signal(update: Update):
    message_text = update.message.text
    chat_id = str(update.message.chat.id)
    chat_title = update.message.chat.title or "Unknown"
    
    logger.info("Processing signal from group %s (%s) with message: %s", chat_id, chat_title, message_text)
    
    db = SessionLocal()
    group = db.query(Group).filter(Group.telegram_group_id == chat_id).first()
    if not group:
        group = Group(telegram_group_id=chat_id, name=chat_title)
        db.add(group)
        db.commit()
        logger.info("Created new group record: %s", chat_title)
    
    subscriptions = db.query(CallAlertSubscription).filter(
        CallAlertSubscription.group_id == group.id,
        CallAlertSubscription.active == True
    ).all()
    
    logger.info("Found %d active subscriptions for group %s", len(subscriptions), chat_title)
    
    for subscription in subscriptions:
        now = datetime.utcnow().time()
        start_time = datetime.strptime(subscription.call_window_start, "%H:%M").time()
        end_time = datetime.strptime(subscription.call_window_end, "%H:%M").time()
        if start_time <= now <= end_time:
            user = subscription.user
            call_message = f"New signal from {group.name}: {message_text}"
            call_sid = initiate_call(user.phone_number, call_message)
            logger.info("Initiated call to %s with SID: %s", user.phone_number, call_sid)
            
            call_log = CallLog(subscription_id=subscription.id, status="initiated", details=call_sid or "failed")
            db.add(call_log)
            db.commit()
        else:
            logger.info("Current UTC time is outside the call window for subscription ID %s", subscription.id)
    db.close()
