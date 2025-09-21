from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
from typing import List
from sqlmodel import Session

from app.dtos.login import LoginData, UserData, NovoUsuario
from app.security.TokenContext import TokenResponse
from app.security.security import gerar_token, pegar_usuario_atual, criar_hash_senha
from app.service.user_services import authenticate_user
from app.repository.user_repository import get_all_users, create_user
from app.domain.user import User
from app.resources.database.connection import get_session


router = APIRouter()

# Rota de login
@router.post("/login", response_model=TokenResponse)
async def login(
    dados_login: LoginData,
    session: Session = Depends(get_session)
):
    usuario = authenticate_user(dados_login, session)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha errados"
        )
    token_expira = timedelta(hours=8)
    access_token = gerar_token(
        dados={"sub": usuario.email},
        tempo_expiracao=token_expira
    )
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# Rota para criar um novo usuário
@router.post("/usuarios", response_model=dict)
async def criar_usuario(
    novo_user: NovoUsuario,
    usuario_atual: User = Depends(pegar_usuario_atual),
    session: Session = Depends(get_session)
):
    if usuario_atual.user_role_id != 1:  # Assumindo que o ID 1 é o admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para isso"
        )

    # Cria a instância do modelo de domínio
    user_to_db = User(
        email=novo_user.email,
        full_name=novo_user.nome,
        password_hash=criar_hash_senha(novo_user.password),
        tipo="usuario"
    )

    # Usa o repositório para salvar no banco
    new_user = create_user(user_to_db, session)

    return {"msg": f"Usuário {new_user.email} criado!", "id": new_user.id}

# Rota para listar todos os usuários
@router.get("/usuarios", response_model=List[UserData])
async def listar_usuarios(
    usuario_atual: User = Depends(pegar_usuario_atual),
    session: Session = Depends(get_session)
):
    if usuario_atual.user_role_id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só administradores podem ver essa informação"
        )

    users = get_all_users(session)

    # Transforma os objetos do banco em objetos de resposta da API
    return [
        UserData(id=user.id, email=user.email, full_name=user.full_name, user_role=user.user_role_id)
        for user in users
    ]


# Rota para ver o perfil
@router.get("/perfil", response_model=UserData)
async def meu_perfil(usuario_atual: User = Depends(pegar_usuario_atual)):
    return UserData(
        id=usuario_atual.id,
        email=usuario_atual.email,
        full_name=usuario_atual.full_name,
        user_role=usuario_atual.user_role_id
    )

# Rota de área restrita
@router.get("/area-restrita")
async def area_restrita(usuario_atual: User = Depends(pegar_usuario_atual)):
    return {
        "msg": f"Olá {usuario_atual.full_name}, você acessou a área restrita!",
        "user_id": usuario_atual.id
    }