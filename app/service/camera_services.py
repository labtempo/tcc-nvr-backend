from sqlmodel import Session
from fastapi import HTTPException, status
from app.domain.camera import Camera
from app.dtos.camera import CamData, CamCreate
from app.repository.camera_repository import create_camera,get_cameras_by_user_id, get_camera_by_name, get_camera_by_id
from typing import List

def criar_camera(camera_data: CamCreate, session: Session) -> Camera:
    if get_camera_by_name(camera_data.name, session):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma câmera com este nome."
        )
    
    camera = Camera(
        name=camera_data.name,
        rtsp_url=camera_data.rtsp_url,
        is_recording=camera_data.is_recording,
        created_by_user_id=camera_data.created_by_user_id
   
    )
    return create_camera(camera, session)

def get_camera(camera_id: int, session: Session) -> Camera:
    if get_camera_by_id(camera_id, session) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada."
        )
    return get_camera_by_id(camera_id, session)


def listar_cameras_por_usuario(user_id: int, session: Session) -> List[Camera]:
    return get_cameras_by_user_id(user_id, session)