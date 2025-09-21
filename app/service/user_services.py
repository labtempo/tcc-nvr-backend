from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.domain.user import User
from app.dtos.login import LoginData
from app.repository.user_repository import get_user_by_email
from app.repository.user_repository import create_user
from app.security.security import criar_hash_senha, verificar_senha
from app.dtos.login import NovoUsuario

def authenticate_user(login_data: LoginData, session: Session) -> User | None:
    user = get_user_by_email(login_data.email, session)
    if not user:
        return None
    if not verificar_senha(login_data.password, user.password_hash):
        return None
    return user

def create_new_user(user_data: NovoUsuario, session: Session) -> User:
    if get_user_by_email(user_data.email, session):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um usuário com este email."
        )
    
    password_hash = criar_hash_senha(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=password_hash,
        nome=user_data.nome,
    )
    
    return create_user(new_user, session)