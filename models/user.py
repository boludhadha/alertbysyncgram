# models/user.py
from sqlalchemy import Column, Integer, String, Boolean
from db.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    active = Column(Boolean, default=True)
