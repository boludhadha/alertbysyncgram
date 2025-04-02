import os
import sqlalchemy
import databases

# Get your external DB URL and ensure it starts with "postgresql://"
EXTERNAL_DATABASE_URL = os.getenv("EXTERNAL_DATABASE_URL")

database = databases.Database(EXTERNAL_DATABASE_URL)
metadata = sqlalchemy.MetaData()

class OrmarConfig:
    def __init__(self, metadata, database):
        self.metadata = metadata
        self.database = database

    def copy(self, **kwargs):
        config = {"metadata": self.metadata, "database": self.database}
        config.update(kwargs)
        return config

base_ormar_config = OrmarConfig(metadata=metadata, database=database)
