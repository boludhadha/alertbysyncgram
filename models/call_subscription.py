# models/call_subscription.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base

class CallAlertSubscription(Base):
    __tablename__ = "call_alert_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    active = Column(Boolean, default=True)
    call_window_start = Column(String, default="00:00")  # Format HH:MM UTC
    call_window_end = Column(String, default="23:59")
    
    user = relationship("User", backref="subscriptions")
    group = relationship("Group", backref="subscriptions")
