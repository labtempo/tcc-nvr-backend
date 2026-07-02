from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

from app.resources.logging import setup_logging, get_logger
from app.controller import recordController, videoController
from app.controller.usersController import router as users
from app.controller.cameraController import router as cameras  
from app.controller.userPreferenceController import router as user_preferences
from app.controller.settingsController import router as settings_router
from app.resources.database.connection import create_db_and_tables, seed_user_roles, engine
from app.controller import playbackController
from sqlmodel import Session, select
from app.domain.system_settings import System_Setting
from app.service.mediaMtx_services import media_mtx_service

# prepare logging antes de qualquer outra coisa
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    seed_user_roles()
    
    # Sincronização no boot com MediaMTX
    try:
        with Session(engine) as session:
            duration_stmt = select(System_Setting).where(System_Setting.setting_key == "record_segment_duration")
            delete_stmt = select(System_Setting).where(System_Setting.setting_key == "record_delete_after")
            
            duration_setting = session.exec(duration_stmt).first()
            delete_setting = session.exec(delete_stmt).first()
            
            segment_duration = duration_setting.setting_value if duration_setting else "1m"
            delete_after = delete_setting.setting_value if delete_setting else "60m"
            
            logger.info(f"Sincronizando configurações globais de gravação com MediaMTX no boot: segment_duration={segment_duration}, delete_after={delete_after}")
            await media_mtx_service.update_global_record_settings(
                record_segment_duration=segment_duration,
                record_delete_after=delete_after
            )
    except Exception as e:
        logger.error(f"Erro ao sincronizar configurações globais de gravação com MediaMTX no boot: {e}")
    
    yield
    pass

app = FastAPI(title="API - OPERAÇÕES", version="1.0", lifespan=lifespan)

origins = [
   "http://localhost:4200",  
    "http://127.0.0.1:4200",  

    "http://localhost:8080",
    "http://127.0.0.1:8080",

    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

app.include_router(users, prefix="/api/v1") 
app.include_router(cameras, prefix="/api/v1")
app.include_router(user_preferences, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(recordController.router, prefix="/api/v1", tags=["records"])
app.include_router(videoController.router)
app.include_router(playbackController.router, prefix="/api/v1")

@app.get("/")
async def home():
    return {
        "sistema": "API - OPERAÇÕES Online", 
        "versao": "1.0",
        "status": "funcionando"
    }

@app.get("/status")
async def verificar_status():
    return {
        "online": True,
        "horario": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "sistema": "API - OPERAÇÕES",
        "versao": "1.0"
    }