from sqlmodel import Session, select
from app.domain.user import User

def buscar_usuario_email(email: str, session: Session):
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()
