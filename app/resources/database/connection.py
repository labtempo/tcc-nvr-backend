import os
from sqlmodel import create_engine, select, SQLModel, Session
from dotenv import load_dotenv
from app.domain.user_role import User_Role, UserRoleEnum
from app.domain.user import User
from app.domain.camera import Camera
from app.domain.record import Record
from app.domain.system_settings import System_Setting
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL env variable is not set.")

engine = create_engine(DATABASE_URL, echo=False)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_db_and_tables():
    logger.info("Criando tabelas no banco de dados...")
    SQLModel.metadata.create_all(engine)
    logger.info("Tabelas criadas com sucesso!")


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