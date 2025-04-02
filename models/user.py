# models/user.py
from sqlalchemy import Column, Integer, String, Boolean
from db.internal_database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=False)
    active = Column(Boolean, default=True)
