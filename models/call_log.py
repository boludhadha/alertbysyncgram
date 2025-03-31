# models/call_log.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from db.database import Base

class CallLog(Base):
    __tablename__ = "call_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("call_alert_subscriptions.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String)   # e.g., initiated, completed, failed
    details = Column(String)  # e.g., Twilio call SID or error details
