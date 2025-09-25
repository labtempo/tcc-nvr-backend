from pydantic import BaseModel, EmailStr
from typing import Optional

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int