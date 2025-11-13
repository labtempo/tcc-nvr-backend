from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

router = APIRouter(
    tags=["Vídeos"]
)

router.mount(
    "/api/v1/videos", 
    StaticFiles(directory="/recordings", html=False), 
    name="videos"
)