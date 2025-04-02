# models/call_log.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from db.internal_database import Base

class CallLog(Base):
    __tablename__ = "call_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("call_alert_subscriptions.id"))
    status = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
