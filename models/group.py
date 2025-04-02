# models/group.py
from sqlalchemy import Column, Integer, String
from db.internal_database import Base

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    telegram_group_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
