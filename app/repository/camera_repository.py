from sqlmodel import Session, select
from app.domain.camera import Camera
from typing import List

def get_camera_by_name(name: str, session: Session):
    statement = select(Camera).where(Camera.name == name)
    return session.exec(statement).first()

def get_camera_by_id(camera_id: int, session: Session):
    statement = select(Camera).where(Camera.id == camera_id)
    return session.exec(statement).first()

def create_camera(camera: Camera, session: Session) -> Camera:
    session.add(camera)
    session.commit()
    session.refresh(camera)
    return camera

def get_cameras_by_user_id(user_id: int, session: Session) -> List[Camera]:
    statement = select(Camera).where(Camera.created_by_user_id == user_id)
    return session.exec(statement).all()