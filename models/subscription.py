import datetime
import ormar
from db.external_ormar_config import base_ormar_config

class Subscription(ormar.Model):
    # Use the syncgram pattern: assign ormar_config via a copy of our base configuration.
    ormar_config = base_ormar_config.copy(tablename="subscriptions")
    
    id: int = ormar.Integer(primary_key=True, autoincrement=True)
    user_id: str = ormar.String(max_length=64)
    group_id: str = ormar.String(max_length=64)
    start_date: datetime.datetime = ormar.DateTime(default=datetime.datetime.utcnow)
    end_date: datetime.datetime = ormar.DateTime(default=datetime.datetime.utcnow)
    owner_id: str = ormar.String(max_length=64)
    invite_link: str = ormar.String(max_length=64, nullable=True)
    invite_used: bool = ormar.Boolean(default=False)
    joined_at: datetime.datetime = ormar.DateTime(nullable=True, timezone=True)
