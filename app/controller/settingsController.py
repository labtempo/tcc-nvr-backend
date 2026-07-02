from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime, timezone
from pydantic import BaseModel

from app.domain.system_settings import System_Setting
from app.domain.user import User
from app.resources.database.connection import get_session
from app.security.security import pegar_usuario_atual
from app.service.mediaMtx_services import media_mtx_service

router = APIRouter()

class GlobalRecordSettingsSchema(BaseModel):
    record_segment_duration: str
    record_delete_after: str

def get_setting_value(session: Session, key: str, default: str) -> str:
    stmt = select(System_Setting).where(System_Setting.setting_key == key)
    setting = session.exec(stmt).first()
    return setting.setting_value if setting else default

def save_setting_value(session: Session, key: str, value: str, description: str = None):
    stmt = select(System_Setting).where(System_Setting.setting_key == key)
    setting = session.exec(stmt).first()
    if setting:
        setting.setting_value = value
        setting.updated_at = datetime.now(timezone.utc)
        if description:
            setting.description = description
    else:
        setting = System_Setting(
            setting_key=key,
            setting_value=value,
            description=description,
            updated_at=datetime.now(timezone.utc)
        )
        session.add(setting)

@router.get("/settings/global", response_model=GlobalRecordSettingsSchema)
def get_global_settings(
    session: Session = Depends(get_session),
    usuario_atual: User = Depends(pegar_usuario_atual)
):
    # Default values: record_segment_duration = "1m", record_delete_after = "60m"
    record_segment_duration = get_setting_value(session, "record_segment_duration", "1m")
    record_delete_after = get_setting_value(session, "record_delete_after", "60m")
    return GlobalRecordSettingsSchema(
        record_segment_duration=record_segment_duration,
        record_delete_after=record_delete_after
    )

@router.put("/settings/global", response_model=GlobalRecordSettingsSchema)
async def update_global_settings(
    settings: GlobalRecordSettingsSchema,
    session: Session = Depends(get_session),
    usuario_atual: User = Depends(pegar_usuario_atual)
):
    if usuario_atual.user_role_id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem alterar as configurações globais de gravação."
        )

    # 1. Update in the DB
    save_setting_value(
        session,
        "record_segment_duration",
        settings.record_segment_duration,
        "Duração de cada segmento de videoclipe gravado"
    )
    save_setting_value(
        session,
        "record_delete_after",
        settings.record_delete_after,
        "Tempo de retenção das gravações"
    )
    session.commit()

    # 2. Call MediaMTX API
    try:
        await media_mtx_service.update_global_record_settings(
            record_segment_duration=settings.record_segment_duration,
            record_delete_after=settings.record_delete_after
        )
    except Exception as e:
        # We raise a bad request/internal server error so the UI/admin knows MediaMTX didn't receive it,
        # but DB was already updated.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Configurações salvas no banco, mas falha ao enviar ao MediaMTX: {str(e)}"
        )

    return settings
