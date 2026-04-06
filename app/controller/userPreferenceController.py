from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.dtos.user_preference import UserCameraOrderUpdate, UserPreferencesResponse
from app.domain.user_preference import UserPreference
from app.resources.database.connection import get_session
from app.security.security import pegar_usuario_atual


router = APIRouter()

@router.put("/users/me/preferences/camera-order", response_model=UserPreferencesResponse)
def update_camera_order(
    request: UserCameraOrderUpdate,
    session: Session = Depends(get_session),
    current_user = Depends(pegar_usuario_atual)
):
    statement = select(UserPreference).where(UserPreference.user_id == current_user.id)
    preference = session.exec(statement).first()
    
    if not preference:
        preference = UserPreference(
            user_id=current_user.id,
            camera_order=request.camera_ids
        )
        session.add(preference)
    else:
       preference.camera_order = request.camera_ids
        
    session.commit()
    session.refresh(preference)
    
    return preference

@router.get("/users/me/preferences", response_model=UserPreferencesResponse)
def get_user_preferences(
    session: Session = Depends(get_session),
    current_user = Depends(pegar_usuario_atual)
):
    statement = select(UserPreference).where(UserPreference.user_id == current_user.id)
    preference = session.exec(statement).first()
    
    if not preference:
        return UserPreferencesResponse(camera_order=[])
        
    return preference
