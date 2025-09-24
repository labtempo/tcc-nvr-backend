from sqlmodel import Session
from fastapi import HTTPException, status
from app.domain.camera import Camera
from app.dtos.camera import CamData, CamCreate
from app.repository.camera_repository import create_camera, get_camera_by_name

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