from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CamCreate(BaseModel):
    name: str
    rtsp_url: str
    is_recording: bool = False
    created_by_user_id: Optional[int] = None

class CamData(CamCreate):
    id: int
    name: str
    rtsp_url: str