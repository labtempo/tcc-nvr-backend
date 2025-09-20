from sqlmodel import Session, select
from app.domain.user import User
from app.security.security import verificar_senha
from app.dtos.login import LoginData

def get_user_by_email(email: str, session: Session) -> User | None:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

def authenticate_user(login_data: LoginData, session: Session) -> User | None:
    user = get_user_by_email(login_data.email, session)
    if not user:
        return None
    if not verificar_senha(login_data.password, user.password_hash):
        return None
    return user