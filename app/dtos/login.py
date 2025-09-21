from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginData(BaseModel):
    email: EmailStr
    password: str

class UserData(BaseModel):
    id: int
    email: str
    full_name: str  
    user_role: int

class NovoUsuario(BaseModel):
    email: EmailStr
    password: str
    full_name: str