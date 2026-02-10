from dotenv import load_dotenv

load_dotenv()

from app.resources.database.connection import get_session
from app.domain.user import User
from app.domain.user_role import UserRoleEnum
from app.security.security import criar_hash_senha
from sqlmodel import select

def seed():
    # Manually create session generator and get session
    session_gen = get_session()
    session = next(session_gen)
    
    email = "admin@sistema.com"
    print(f"Checking for user {email}...")
    
    statement = select(User).where(User.email == email)
    existing = session.exec(statement).first()
    
    if existing:
        print("Admin user already exists!")
        return

    print("Creating Admin user...")
    admin_user = User(
        email=email,
        password_hash=criar_hash_senha("admin123"),
        full_name="Administrador",
        user_role_id=1, # Admin
        is_active=True
    )
    
    session.add(admin_user)
    session.commit()
    print("Admin user created successfully!")

if __name__ == "__main__":
    seed()
