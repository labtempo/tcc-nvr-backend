import sys
import os
sys.path.append(os.getcwd())
# Force DATABASE_URL for local execution (assuming default docker-compose ports)
os.environ["DATABASE_URL"] = "postgresql://tcc_usr:tcc_pwd@localhost:5433/tcc_db"
from app.resources.database.connection import engine
from sqlmodel import Session, select
from app.domain.user import User

def list_users():
    print("Connecting to DB...")
    with Session(engine) as session:
        statement = select(User)
        results = session.exec(statement).all()
        print(f"Found {len(results)} users:")
        for user in results:
            print(f"ID: {user.id} | Email: {user.email} | Name: {user.full_name} | Role: {user.user_role_id}")
            # Note: Password is hashed, we can't see it, but we can assume 'admin' or reset it if needed.
            # But just knowing the Email is key.

if __name__ == "__main__":
    list_users()
