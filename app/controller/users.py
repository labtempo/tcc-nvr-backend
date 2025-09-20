from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
from app.dtos.login import LoginData, UserData, NovoUsuario
from app.security.TokenContext import TokenResponse
from app.security.security import fazer_login, gerar_token, pegar_usuario_atual, TOKEN_EXPIRE_HOURS, buscar_usuario_email, criar_hash_senha, usuarios
from typing import List

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(dados_login: LoginData):
    usuario = fazer_login(dados_login.email, dados_login.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha errados"
        )
    token_expira = timedelta(hours=TOKEN_EXPIRE_HOURS)
    access_token = gerar_token(
        dados={"sub": usuario["email"]}, 
        tempo_expiracao=token_expira
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }


@router.get("/perfil", response_model=UserData)
async def meu_perfil(usuario_atual: dict = Depends(pegar_usuario_atual)):
    return UserData(
        id=usuario_atual["id"],
        email=usuario_atual["email"],
        nome=usuario_atual["nome"],
        tipo=usuario_atual["tipo"]
    )

@router.get("/area-restrita")
async def area_restrita(usuario_atual: dict = Depends(pegar_usuario_atual)):
    return {
        "msg": f"Olá {usuario_atual['nome']}, você acessou a área restrita!",
        "user_id": usuario_atual["id"]
    }

@router.get("/usuarios", response_model=List[dict])
async def listar_usuarios(usuario_atual: dict = Depends(pegar_usuario_atual)):
    if usuario_atual["tipo"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só administradores podem ver essa informação"
        )
    lista_usuarios = []
    for email, dados_user in usuarios.items():
        lista_usuarios.append({
            "id": dados_user["id"],
            "email": dados_user["email"], 
            "nome": dados_user["nome"],
            "tipo": dados_user["tipo"]
        })
    return lista_usuarios

@router.post("/usuarios", response_model=dict)
async def criar_usuario(novo_user: NovoUsuario, usuario_atual: dict = Depends(pegar_usuario_atual)):
    if usuario_atual["tipo"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para isso"
        )
    if buscar_usuario_email(novo_user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe usuário com esse email"
        )
    proximo_id = max([user["id"] for user in usuarios.values()]) + 1
    usuarios[novo_user.email] = {
        "id": proximo_id,
        "email": novo_user.email,
        "nome": novo_user.nome,
        "senha_hash": criar_hash_senha(novo_user.password),
        "tipo": "usuario"
    }
    return {"msg": f"Usuário {novo_user.email} criado!", "id": proximo_id}