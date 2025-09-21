from fastapi import FastAPI
from app.controller.users import router as users
from app.resources.database.connection import create_db_and_tables
from datetime import datetime

app = FastAPI(title="API - OPERAÇÕES", version="1.0")

app.include_router(users, prefix="/api/v1") 

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

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