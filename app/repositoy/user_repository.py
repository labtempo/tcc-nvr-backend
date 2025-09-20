from sqlmodel import Session, select
from app.domain.user import User

def get_user_by_email(email: str, session: Session) -> User | None:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

def create_user(user: User, session: Session) -> User:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user