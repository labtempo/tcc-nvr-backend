from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session
from app.dtos.camera import CamCreate, CamData
from app.domain.camera import Camera
from app.resources.database.connection import get_session
from app.service.camera_services import criar_camera

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