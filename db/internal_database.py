# db/internal_database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use the PostgreSQL URL from your environment variable.
INTERNAL_DATABASE_URL = os.getenv("INTERNAL_DATABASE_URL")

engine = create_engine(INTERNAL_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
