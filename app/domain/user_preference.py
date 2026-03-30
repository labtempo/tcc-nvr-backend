from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON

class UserPreference(SQLModel, table=True):
    __tablename__ = "user_preferences"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, unique=True, foreign_key="user.id")

    camera_order: List[int] = Field(default=[], sa_column=Column(JSON))

    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
