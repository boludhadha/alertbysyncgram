# models/call_subscription.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.internal_database import Base

class CallAlertSubscription(Base):
    __tablename__ = "call_alert_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    active = Column(Boolean, default=False)  # Inactive until payment confirmation
    call_window_start = Column(String, default="00:00")
    call_window_end = Column(String, default="23:59")
    
    # Use fully qualified name for the User model.
    user = relationship("models.user.User")
    # Similarly, for the Group model, assuming it is in models/group.py.
    group = relationship("models.group.Group")
