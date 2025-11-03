from sqlmodel import Session
from fastapi import HTTPException, status
from app.domain.camera import Camera
from app.dtos.camera import CamCreate
from app.repository.camera_repository import create_camera, get_cameras_by_user_id, get_camera_by_name, get_camera_by_id
from typing import List

async def criar_camera(camera_data: CamCreate, session: Session) -> Camera:
    if get_camera_by_name(camera_data.name, session):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma câmera com este nome."
        )
    
    path_id = f"live/{camera_data.name.lower().replace(' ', '_')}"
    
    from app.service.mediaMtx_services import media_mtx_service
    
    try:
        path_is_ready = await media_mtx_service.create_and_verify_camera_path(
            path_name=path_id,
            rtsp_url=camera_data.rtsp_url
        )
        if not path_is_ready:
            raise HTTPException(status_code=503, detail="Não foi possível configurar o stream no MediaMTX.")
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=f"Timeout ao configurar stream: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erro no MediaMTX: {e}")

    camera = Camera(
        name=camera_data.name,
        rtsp_url=camera_data.rtsp_url,
        is_recording=camera_data.is_recording,
        created_by_user_id=camera_data.created_by_user_id,
        path_id=path_id
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