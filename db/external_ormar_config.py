import os
from sqlalchemy import create_engine, MetaData
from databases import Database

EXTERNAL_DATABASE_URL = os.getenv("EXTERNAL_DATABASE_URL")
metadata = MetaData()
database = Database(EXTERNAL_DATABASE_URL)
engine = create_engine(EXTERNAL_DATABASE_URL)
