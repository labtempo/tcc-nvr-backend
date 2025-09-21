from sqlmodel import Session, select
from app.domain.camera import Camera

def get_camera_by_name(name: str, session: Session):
    statement = select(Camera).where(Camera.name == name)
    return session.exec(statement).first()

def create_camera(camera: Camera, session: Session) -> Camera:
    session.add(camera)
    session.commit()
    session.refresh(camera)
    return camera
