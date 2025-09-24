from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session
from app.dtos.camera import CamCreate, CamData
from app.domain.camera import Camera
from app.resources.database.connection import get_session
from app.service.camera_services import criar_camera, get_camera, listar_cameras_por_usuario
from typing import List

router = APIRouter()

@router.post("/camera", response_model=CamData)
async def adicionar_camera(
    dados_camera: CamCreate,
    session: Session = Depends(get_session)
):
    nova_camera = criar_camera(dados_camera, session)
    return CamData(
        id=nova_camera.id,
        name=nova_camera.name,
        rtsp_url=nova_camera.rtsp_url,
        is_recording=nova_camera.is_recording,
        created_by_user_id=nova_camera.created_by_user_id,
        created_at=nova_camera.created_at,
        updated_at=nova_camera.updated_at
    )

@router.get("/camera/{camera_id}", response_model=CamData)
async def obter_camera(camera_id: int, session: Session = Depends(get_session)):
    camera = get_camera(camera_id, session)
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada"
        )
    return CamData(
        id=camera.id,
        name=camera.name,
        rtsp_url=camera.rtsp_url,
        is_recording=camera.is_recording,
        created_by_user_id=camera.created_by_user_id,
        created_at=camera.created_at,
        updated_at=camera.updated_at
    )

@router.get("/camera/user/{user_id}", response_model=List[CamData])
async def listar_cameras_usuario(user_id: int, session: Session = Depends(get_session)):
    cameras = listar_cameras_por_usuario(user_id, session)
    return [
        CamData(
            id=camera.id,
            name=camera.name,
            rtsp_url=camera.rtsp_url,
            is_recording=camera.is_recording,
            created_by_user_id=camera.created_by_user_id,
            created_at=camera.created_at,
            updated_at=camera.updated_at
        )
        for camera in cameras
    ]