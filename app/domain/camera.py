from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Relationship

class Camera(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    rtsp_url: str
    is_recording: bool = Field(default=False)
    created_by_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))