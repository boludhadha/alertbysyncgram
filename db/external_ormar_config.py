# db/external_ormar_config.py
import os
import sqlalchemy
from sqlalchemy import create_engine
from databases import Database

# Retrieve the external database URL from the environment.
EXTERNAL_DATABASE_URL = os.getenv("EXTERNAL_DATABASE_URL")
# Ensure the URL uses the correct scheme.
EXTERNAL_DATABASE_URL = str(EXTERNAL_DATABASE_URL).replace("postgres://", "postgresql://", 1)

# Create the SQLAlchemy metadata and the asynchronous Database instance.
database = Database(EXTERNAL_DATABASE_URL)
metadata = sqlalchemy.MetaData()


# Create an engine if needed (for synchronous operations)
engine = create_engine(EXTERNAL_DATABASE_URL)
