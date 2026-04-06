from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
from typing import List
from sqlmodel import Session

from app.dtos.login import LoginData, UserData, NovoUsuario
from app.resources.logging.logger import get_logger
from app.security.TokenContext import TokenResponse
from app.security.security import gerar_token, pegar_usuario_atual, criar_hash_senha
from app.service.user_services import authenticate_user
from app.repository.user_repository import get_all_users, create_user, delete_user
from app.domain.user import User
from app.resources.database.connection import get_session

router = APIRouter()
logger = get_logger(__name__)

@router.post("/login", response_model=TokenResponse)
async def login(
    dados_login: LoginData,
    session: Session = Depends(get_session)
):
    
    logger.info(f"Tentativa de login recebida para o usuário: {dados_login.email}")

    usuario = authenticate_user(dados_login, session)
    if not usuario:
        logger.warning(f"Falha de autenticação para o usuário: {dados_login.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha errados"
        )
    token_expira = timedelta(hours=8)
    access_token = gerar_token(
        dados={"sub": usuario.email},
        tempo_expiracao=token_expira
    )
    role_name = "admin" if usuario.user_role_id == 1 else "viewer"

    logger.info(f"Login realizado com sucesso para: {dados_login.email} (Role: {role_name})")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": usuario.id,
        "role": role_name
    }

@router.post("/usuarios", response_model=dict)
async def criar_usuario(
    novo_user: NovoUsuario,
    usuario_atual: User = Depends(pegar_usuario_atual),
    session: Session = Depends(get_session)
):
    if usuario_atual.user_role_id != 1: 
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para criar usuários. Apenas administradores."
        )

    user_to_db = User(
        email=novo_user.email,
        full_name=novo_user.full_name,
        password_hash=criar_hash_senha(novo_user.password),
        user_role_id=2
    )

    new_user = create_user(user_to_db, session)

    return {"msg": f"Usuário {new_user.email} criado com função de Visualizador!", "id": new_user.id}

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

    return [
        UserData(
            id=user.id, 
            email=user.email, 
            full_name=user.full_name, 
            user_role=user.user_role_id,
            role="admin" if user.user_role_id == 1 else "viewer"
        )
        for user in users
    ]

@router.get("/perfil", response_model=UserData)
async def meu_perfil(usuario_atual: User = Depends(pegar_usuario_atual)):
    return UserData(
        id=usuario_atual.id,
        email=usuario_atual.email,
        full_name=usuario_atual.full_name,
        user_role=usuario_atual.user_role_id,
        role="admin" if usuario_atual.user_role_id == 1 else "viewer"
    )

@router.get("/area-restrita")
async def area_restrita(usuario_atual: User = Depends(pegar_usuario_atual)):
    return {
        "msg": f"Olá {usuario_atual.full_name}, você acessou a área restrita!",
        "user_id": usuario_atual.id
    }

@router.delete("/usuarios/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_usuario(
    user_id: int,
    usuario_atual: User = Depends(pegar_usuario_atual),
    session: Session = Depends(get_session)
):
    if usuario_atual.user_role_id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem deletar usuários."
        )

    if usuario_atual.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode deletar a si mesmo."
        )

    user_to_delete = session.get(User, user_id)
    
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )

    delete_user(user_to_delete, session)
    return None
