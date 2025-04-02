# models/call_subscription.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.internal_database import Base

class CallAlertSubscription(Base):
    __tablename__ = "call_alert_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    active = Column(Boolean, default=False)  # becomes active after payment confirmation
    call_window_start = Column(String, default="00:00")
    call_window_end = Column(String, default="23:59")
    
    user = relationship("User")
    group = relationship("Group")
