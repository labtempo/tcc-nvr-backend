from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controller.users import router as users
from app.controller.camera import router as cameras  
from app.resources.database.connection import create_db_and_tables, seed_user_roles
from datetime import datetime

app = FastAPI(title="API - OPERAÇÕES", version="1.0")

#-------------//-------------//

origins = [
    "http://localhost:4200",  
    "http://127.0.0.1:4200",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)
#----------//-----------------//

app.include_router(users, prefix="/api/v1") 
app.include_router(cameras, prefix="/api/v1")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    seed_user_roles()

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