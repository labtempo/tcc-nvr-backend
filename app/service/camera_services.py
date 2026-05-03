from sqlmodel import Session
from fastapi import HTTPException, status
from app.domain.camera import Camera
from app.dtos.camera import CamCreate
from app.repository.camera_repository import create_camera, get_cameras_by_user_id, get_camera_by_name, get_camera_by_id, delete_camera, get_all_cameras
from typing import List

async def criar_camera(camera_data: CamCreate, session: Session) -> Camera:
    if get_camera_by_name(camera_data.name, session):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma câmera com este nome."
        )
    
    path_id = camera_data.path_id if camera_data.path_id else camera_data.name.strip().replace(' ', '_')
    path_id_low = camera_data.path_id_low if camera_data.path_id_low else None
    
    from app.service.mediaMtx_services import media_mtx_service
    
    try:
        # Criar path principal
        path_is_ready = await media_mtx_service.create_and_verify_camera_path(
            path_name=path_id,
            rtsp_url=camera_data.rtsp_url,
            record=camera_data.is_recording
        )
        if not path_is_ready:
            raise HTTPException(status_code=503, detail="Não foi possível configurar o stream no MediaMTX.")
        
        # Se URL de baixa qualidade foi fornecida, criar path para isso também
        if camera_data.rtsp_url_low and path_id_low:
            try:
                low_quality_ready = await media_mtx_service.create_and_verify_camera_path(
                    path_name=path_id_low,
                    rtsp_url=camera_data.rtsp_url_low,
                    record=camera_data.is_recording
                )
                if not low_quality_ready:
                    print(f"AVISO: Não foi possível configurar stream de baixa qualidade para {path_id_low}")
            except Exception as e:
                print(f"AVISO: Erro ao configurar stream de baixa qualidade: {e}")
                # Continua mesmo se falhar na baixa qualidade
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=f"Timeout ao configurar stream: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erro no MediaMTX: {e}")

    camera = Camera(
        name=camera_data.name,
        rtsp_url=camera_data.rtsp_url,
        rtsp_url_low=camera_data.rtsp_url_low,
        is_recording=camera_data.is_recording,
        created_by_user_id=camera_data.created_by_user_id,
        path_id=path_id,
        path_id_low=path_id_low
    )
    return create_camera(camera, session)

def get_camera(camera_id: int, session: Session) -> Camera:
    if get_camera_by_id(camera_id, session) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada."
        )
    return get_camera_by_id(camera_id, session)

async def deletar_camera(camera_id: int, session: Session) -> bool:
    """Deleta uma câmera e seu path no MediaMTX"""
    camera = get_camera_by_id(camera_id, session)
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Câmera não encontrada."
        )
    
    # Primeiro tenta deletar o path do MediaMTX
    from app.service.mediaMtx_services import media_mtx_service
    
    try:
        await media_mtx_service.delete_camera_path(camera.path_id)
    except Exception as e:
        print(f"AVISO: Erro ao deletar path do MediaMTX: {e}")
        # Continua com a deleção no banco mesmo se falhar no MediaMTX
    
    # Deleta a câmera do banco de dados
    try:
        delete_camera(camera, session)
        return True
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao deletar câmera do banco de dados: {e}"
        )

def listar_cameras_por_usuario(user_id: int, session: Session) -> List[Camera]:
    return get_cameras_by_user_id(user_id, session)

def listar_todas_cameras(session: Session) -> List[Camera]:
    return get_all_cameras(session)