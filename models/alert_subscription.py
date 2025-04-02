# models/alert_subscription.py
import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from db.internal_database import Base

class AlertSubscription(Base):
    __tablename__ = "alert_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    telegram_user_id = Column(String, nullable=False, index=True)
    group_id = Column(String, nullable=False, index=True)  # This should match the group_id from external subscription
    phone_number = Column(String, nullable=False)
    subscription_start = Column(DateTime, default=datetime.datetime.utcnow)
    subscription_end = Column(DateTime, nullable=False)  # e.g., subscription valid for 30 days
    active = Column(Boolean, default=True)
