from pydantic import BaseModel, EmailStr
from typing import Optional

class CamData(BaseModel):
    id: int
    name: str
    rtsp_url: str
    is_recording: bool
    description: Optional[str] = None
    user_id: int