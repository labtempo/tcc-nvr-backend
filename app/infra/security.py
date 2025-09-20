from datetime import datetime, timedelta
from typing import Optional
import hashlib
import jwt
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# --- CONFIGS ---
JWT_SECRET = "kjh87asd6f7asd6f87asd6f78asd6f8asd7f6asd78f6asd7f6"
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 8
security = HTTPBearer()

# --- DADOS MOCK (DEPOIS VAI PARA O BANCO) ---
usuarios = {
    "admin@sistema.com": {
        "id": 1,
        "email": "admin@sistema.com",
        "nome": "Administrator",
        "senha_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",
        "tipo": "admin"
    }
}

# --- FUNÇÕES DE SEGURANÇA ---
def criar_hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_senha(senha_texto: str, senha_hash: str) -> bool:
    return criar_hash_senha(senha_texto) == senha_hash

def gerar_token(dados: dict, tempo_expiracao: Optional[timedelta] = None):
    payload = dados.copy()
    if tempo_expiracao:
        expira = datetime.utcnow() + tempo_expiracao
    else:
        expira = datetime.utcnow() + timedelta(hours=1)
    payload.update({"exp": expira})
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

async def pegar_usuario_atual(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
    user = buscar_usuario_email(email)
    if user is None:
        raise erro_auth
    return user
    
def buscar_usuario_email(email: str):
    return usuarios.get(email)

def fazer_login(email: str, senha: str):
    user = buscar_usuario_email(email)
    if not user:
        return None
    if not verificar_senha(senha, user["senha_hash"]):
        return None
    return user