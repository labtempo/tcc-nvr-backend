from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session
from app.dtos.camera import CamData
from app.domain.camera import Camera
from app.resources.database.connection import get_session

router = APIRouter()

@router.post("/camera")
async def adicionar_camera(
    dados_camera: CamData,
    session: Session = Depends(get_session)
):