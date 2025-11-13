import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from app.domain.user import User
from app.resources.settings.config import settings
from app.resources.database.connection import get_session
from datetime import datetime, timedelta, timezone
from app.repository.login_repository import buscar_usuario_email
from jose import JWTError, jwt

# --- CONFIGS ---
JWT_SECRET = "kjh87asd6f7asd6f87asd6f78asd6f8asd7f6asd78f6asd7f6"
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 8
security = HTTPBearer()

# --- FUNÇÕES DE SEGURANÇA ---
def criar_hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_senha(senha_texto: str, senha_hash: str) -> bool:
    return criar_hash_senha(senha_texto) == senha_hash

def gerar_token(dados: dict, tempo_expiracao: Optional[timedelta] = None):
    payload = dados.copy()
    if tempo_expiracao:
        expira = datetime.now(timezone.utc) + tempo_expiracao
    else:
        expira = datetime.now(timezone.utc) + timedelta(hours=1)
    payload.update({"exp": expira})
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

async def pegar_usuario_atual(credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)):
    erro_auth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise erro_auth
    except jwt.PyJWTError:
        raise erro_auth
    user = buscar_usuario_email(email, session)
    if user is None:
        raise erro_auth
    return user
    
def fazer_login(email: str, senha: str, session: Session):
    user = buscar_usuario_email(email, session)
    if not user:
        return None
    if not verificar_senha(senha, user.password_hash):
        return None
    return user

def create_temp_playback_token(data: dict) -> str:
    """
    Cria um JWT de curta duração para autorizar o stream de playback.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        seconds=settings.PLAYBACK_TOKEN_EXPIRE_SECONDS
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.PLAYBACK_TOKEN_SECRET_KEY, 
        algorithm=settings.PLAYBACK_TOKEN_ALGORITHM
    )
    return encoded_jwt

def decode_temp_playback_token(token: str) -> dict:
    """
    Valida o token de playback temporário.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.PLAYBACK_TOKEN_SECRET_KEY, 
            algorithms=[settings.PLAYBACK_TOKEN_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de playback inválido ou expirado"
        )