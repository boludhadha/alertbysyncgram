# db/external_ormar_config.py
import os
from sqlalchemy import create_engine, MetaData
from databases import Database

# Use the PostgreSQL URL from your environment variable.
EXTERNAL_DATABASE_URL = os.getenv("EXTERNAL_DATABASE_URL")
metadata = MetaData()
engine = create_engine(EXTERNAL_DATABASE_URL)
database = Database(EXTERNAL_DATABASE_URL)

base_ormar_config = {
    "database": database,
    "metadata": metadata,
    "engine": engine,
}
