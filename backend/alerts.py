# backend/alerts.py
from telegram import Update
from db.database import SessionLocal
from models.group import Group
from models.call_subscription import CallAlertSubscription
from models.call_log import CallLog
from backend.call_service import initiate_call
from datetime import datetime

def process_signal(update: Update):
    """
    Process a Telegram signal message and trigger calls to subscribers.
    """
    message_text = update.message.text
    chat_id = str(update.message.chat.id)
    chat_title = update.message.chat.title or "Unknown"
    
    db = SessionLocal()
    
    # Ensure the group exists.
    group = db.query(Group).filter(Group.telegram_group_id == chat_id).first()
    if not group:
        group = Group(telegram_group_id=chat_id, name=chat_title)
        db.add(group)
        db.commit()
    
    # Fetch active subscriptions for the group.
    subscriptions = db.query(CallAlertSubscription).filter(
        CallAlertSubscription.group_id == group.id,
        CallAlertSubscription.active == True
    ).all()
    
    for subscription in subscriptions:
        # Check if the current UTC time is within the user's call window.
        now = datetime.utcnow().time()
        start_time = datetime.strptime(subscription.call_window_start, "%H:%M").time()
        end_time = datetime.strptime(subscription.call_window_end, "%H:%M").time()
        if start_time <= now <= end_time:
            user = subscription.user  # thanks to the relationship defined in the model
            call_message = f"New signal from {group.name}: {message_text}"
            call_sid = initiate_call(user.phone_number, call_message)
            
            # Log the call event.
            call_log = CallLog(subscription_id=subscription.id, status="initiated", details=call_sid or "failed")
            db.add(call_log)
            db.commit()
    
    db.close()
