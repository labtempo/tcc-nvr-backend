from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import jwt
from datetime import datetime, timedelta
import hashlib

app = FastAPI(title="API Sistema", version="1.0")

# configs gerais
JWT_SECRET = "kjh87asd6f7asd6f87asd6f78asd6f8asd7f6asd78f6asd7f6"
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 8

security = HTTPBearer()

# usuarios do sistema - depois vai pro banco de dados
usuarios = {
    "admin@sistema.com": {
        "id": 1,
        "email": "admin@sistema.com",
        "nome": "Administrator",
        "senha_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # admin123
        "tipo": "admin"
    }
}

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

def buscar_usuario_email(email: str):
    return usuarios.get(email)

def fazer_login(email: str, senha: str):
    user = buscar_usuario_email(email)
    if not user:
        return None
    
    if not verificar_senha(senha, user["senha_hash"]):
        return None
    
    return user

async def pegar_usuario_atual(credentials: HTTPAuthorizationCredentials = Depends(security)):
    erro_auth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalido",
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

@app.get("/")
async def home():
    return {
        "sistema": "API Online", 
        "versao": "1.0",
        "status": "funcionando"
    }

@app.post("/login", response_model=TokenResponse)
async def login(dados_login: LoginData):
    usuario = fazer_login(dados_login.email, dados_login.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha errados"
        )
    
    # token valido por 8 horas
    token_expira = timedelta(hours=TOKEN_EXPIRE_HOURS)
    access_token = gerar_token(
        dados={"sub": usuario["email"]}, 
        tempo_expiracao=token_expira
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }

@app.get("/perfil", response_model=UserData)
async def meu_perfil(usuario_atual = Depends(pegar_usuario_atual)):
    return UserData(
        id=usuario_atual["id"],
        email=usuario_atual["email"],
        nome=usuario_atual["nome"],
        tipo=usuario_atual["tipo"]
    )

@app.get("/area-restrita")
async def area_restrita(usuario_atual = Depends(pegar_usuario_atual)):
    return {
        "msg": f"Ola {usuario_atual['nome']}, voce acessou a area restrita!",
        "user_id": usuario_atual["id"],
        "acesso_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

@app.get("/usuarios")
async def listar_usuarios(usuario_atual = Depends(pegar_usuario_atual)):
    # so admin pode ver lista de usuarios
    if usuario_atual["tipo"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só administradores podem ver essa informacao"
        )
    
    lista_usuarios = []
    for email, dados_user in usuarios.items():
        lista_usuarios.append({
            "id": dados_user["id"],
            "email": dados_user["email"], 
            "nome": dados_user["nome"],
            "tipo": dados_user["tipo"]
        })
    
    return {"usuarios": lista_usuarios, "total": len(lista_usuarios)}

@app.post("/usuarios")
async def criar_usuario(novo_user: NovoUsuario, usuario_atual = Depends(pegar_usuario_atual)):
    # só admin pode criar usuarios
    if usuario_atual["tipo"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce nao tem permissao para isso"
        )
    
    # verifica se ja existe
    if buscar_usuario_email(novo_user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ja existe usuario com esse email"
        )
    
    # pega o proximo id
    proximo_id = max([user["id"] for user in usuarios.values()]) + 1
    
    # adiciona o usuario
    usuarios[novo_user.email] = {
        "id": proximo_id,
        "email": novo_user.email,
        "nome": novo_user.nome,
        "senha_hash": criar_hash_senha(novo_user.password),
        "tipo": "usuario"  # novos usuarios sempre sao tipo usuario
    }
    
    return {"msg": f"Usuario {novo_user.email} criado!", "id": proximo_id}

@app.get("/status")
async def verificar_status():
    return {
        "online": True,
        "horario": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "sistema": "API Sistema",
        "versao": "1.0"
    }

if __name__ == "__main__":
    import uvicorn
    
    print("Iniciando servidor...")
    print("URL: http://localhost:8000")
    print("Documentacao: http://localhost:8000/docs")
    print("")
    print("Usuarios para teste:")
    print("admin@sistema.com / admin123")
    print("joao@sistema.com / user123")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)