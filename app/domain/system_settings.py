from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel

class System_Setting(SQLModel, table=True):
    setting_key: str = Field(primary_key=True)
    setting_value: str
    description: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))