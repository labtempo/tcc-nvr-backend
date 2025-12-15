import sys
import os
sys.path.append(os.getcwd())
# Force DATABASE_URL
os.environ["DATABASE_URL"] = "postgresql://tcc_usr:tcc_pwd@localhost:5433/tcc_db"
# Mock other env vars to satisfy Settings validation
os.environ["MEDIA_MTX_HOST"] = "http://localhost"
os.environ["CONTROL_API_PORT"] = "9997"
os.environ["HLS_PORT"] = "8888"
os.environ["WEBRTC_PORT"] = "8889"
os.environ["MEDIAMTX_API_USER"] = "user"
os.environ["MEDIAMTX_API_PASS"] = "pass"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

from app.resources.database.connection import engine
from sqlmodel import Session, select
from app.domain.user import User
from app.security.security import criar_hash_senha

def create_tester():
    print("Connecting to DB to create test user...")
    with Session(engine) as session:
        # Check if exists
        statement = select(User).where(User.email == "tester@test.com")
        existing = session.exec(statement).first()
        if existing:
            print("User tester@test.com already exists. Updating password...")
            existing.password_hash = criar_hash_senha("test")
            session.add(existing)
            session.commit()
            print("Password updated to 'test'.")
            return

        new_user = User(
            email="tester@test.com",
            full_name="Stress Tester",
            password_hash=criar_hash_senha("test"),
            user_role_id=1 # Admin
        )
        session.add(new_user)
        session.commit()
        print(f"Created user tester@test.com (ID: {new_user.id})")

if __name__ == "__main__":
    create_tester()
