import os
from sqlmodel import create_engine, SQLModel, Session
from dotenv import load_dotenv
from app.domain.user import User
from app.domain.camera import Camera
from app.domain.user_role import User_Role
from app.domain.system_settings import System_Setting

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL env variable is not set.")

engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    print("Criando tabelas no banco de dados...")
    SQLModel.metadata.create_all(engine)
    print("Tabelas criadas com sucesso!")

def get_session():
    with Session(engine) as session:
        yield session