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
    path_id: str
    path_id_low: Optional[str] = None
    visualisation_url_hls: str 
    visualisation_url_hls_low: Optional[str] = None 
    visualisation_url_webrtc: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None 
