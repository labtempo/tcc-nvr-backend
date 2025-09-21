import os
from sqlmodel import create_engine, select, SQLModel, Session
from dotenv import load_dotenv
from app.domain.user import User
from app.domain.camera import Camera
from app.domain.user_role import User_Role
from app.domain.system_settings import System_Setting
from app.domain.user_role import User_Role, UserRoleEnum
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL env variable is not set.")

engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    print("Criando tabelas no banco de dados...")
    SQLModel.metadata.create_all(engine)
    print("Tabelas criadas com sucesso!")


def seed_user_roles():
    with Session(engine) as session:
        for role in UserRoleEnum:
            exists = session.exec(
                select(User_Role).where(User_Role.role_name == role.value)
            ).first()
            if not exists:
                session.add(User_Role(role_name=role.value, description=f"Tipo {role.value}"))
        session.commit()    

def get_session():
    with Session(engine) as session:
        yield session