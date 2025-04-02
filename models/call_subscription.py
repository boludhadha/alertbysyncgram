# models/call_subscription.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.internal_database import Base
from models.user import User  # Import the User model explicitly
from models.group import Group  # Import the Group model explicitly

class CallAlertSubscription(Base):
    __tablename__ = "call_alert_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    active = Column(Boolean, default=False)
    call_window_start = Column(String, default="00:00")
    call_window_end = Column(String, default="23:59")
    
    # Directly reference the classes
    user = relationship(User)
    group = relationship(Group)
