from pydantic import BaseModel
from typing import List

class UserCameraOrderUpdate(BaseModel):
    camera_ids: List[int]

class UserPreferencesResponse(BaseModel):
    camera_order: List[int]