from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

from app.controller import recordController, videoController
from app.controller.usersController import router as users
from app.controller.cameraController import router as cameras  
from app.resources.database.connection import create_db_and_tables, seed_user_roles
from app.controller import playbackController

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    seed_user_roles()
    
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