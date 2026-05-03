from pydantic import BaseModel, EmailStr
from typing import List, Optional

class LoginData(BaseModel):
    email: EmailStr
    password: str

class UserData(BaseModel):
    id: int
    email: str
    full_name: str  
    user_role: int
    role: str
    camera_order: Optional[List[int]] = []

class NovoUsuario(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class AtualizarUsuario(BaseModel):
    password: str