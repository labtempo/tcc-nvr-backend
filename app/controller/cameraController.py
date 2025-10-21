from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session
from app.dtos.camera import CamCreate, CamData
from app.domain.camera import Camera
from app.resources.database.connection import get_session
from app.service.camera_services import criar_camera, get_camera, listar_cameras_por_usuario
from typing import List
from app.resources.settings.config import settings 
from app.service.mediaMtx_services import media_mtx_service 

router = APIRouter()

@router.post("/camera", response_model=CamData)
async def adicionar_camera(
    dados_camera: CamCreate,
    session: Session = Depends(get_session)
):
    try:
        nova_camera = await criar_camera(dados_camera, session)
    
        hls_url = f"{settings.media_mtx_hls_url}/{nova_camera.path_id}/index.m3u8"

        return CamData(
            id=nova_camera.id,
            name=nova_camera.name,
            rtsp_url=nova_camera.rtsp_url,
            is_recording=nova_camera.is_recording,
            created_by_user_id=nova_camera.created_by_user_id,
            created_at=nova_camera.created_at,
            updated_at=nova_camera.updated_at,
            visualisation_url_hls=hls_url
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Um erro inesperado ocorreu: {str(e)}"
        )

@router.get("/camera/{camera_id}", response_model=CamData)
async def obter_camera(camera_id: int, session: Session = Depends(get_session)):
    camera = get_camera(camera_id, session)
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada"
        )
    
    hls_url = f"{settings.media_mtx_hls_url}/{camera.path_id}/index.m3u8"

    return CamData(
        id=camera.id,
        name=camera.name,
        rtsp_url=camera.rtsp_url,
        is_recording=camera.is_recording,
        created_by_user_id=camera.created_by_user_id,
        created_at=camera.created_at,
        updated_at=camera.updated_at,
        visualisation_url_hls=hls_url
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
            updated_at=camera.updated_at,
            visualisation_url_hls=f"{settings.media_mtx_hls_url}/{camera.path_id}/index.m3u8" 
        )
        for camera in cameras
    ]

@router.put("/camera/{camera_id}", response_model=CamData)
async def atualizar_camera(
    camera_id: int,
    dados_camera: CamCreate,
    session: Session = Depends(get_session)
):
    camera = get_camera(camera_id, session)
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada"
        )
    rtsp_url_changed = camera.rtsp_url != dados_camera.rtsp_url
    if rtsp_url_changed:
        try:
            await media_mtx_service.create_camera_path(camera.path_id, dados_camera.rtsp_url)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Falha ao reconfigurar stream no MediaMTX: {e}" 
            )

    camera.name = dados_camera.name
    camera.rtsp_url = dados_camera.rtsp_url
    camera.is_recording = dados_camera.is_recording
    camera.created_by_user_id = dados_camera.created_by_user_id

    session.add(camera)
    session.commit()
    session.refresh(camera)

    hls_url = f"{settings.media_mtx_hls_url}/{camera.path_id}/index.m3u8"

    return CamData(
        id=camera.id,
        name=camera.name,
        rtsp_url=camera.rtsp_url,
        is_recording=camera.is_recording,
        created_by_user_id=camera.created_by_user_id,
        created_at=camera.created_at,
        updated_at=camera.updated_at,
        visualisation_url_hls=hls_url 
    )