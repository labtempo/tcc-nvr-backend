from pydantic import BaseModel, EmailStr
from typing import Optional

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class LoginData(BaseModel):
    email: EmailStr
    password: str

class UserData(BaseModel):
    id: int
    email: str
    nome: str
    tipo: str

class NovoUsuario(BaseModel):
    email: EmailStr
    password: str
    nome: str