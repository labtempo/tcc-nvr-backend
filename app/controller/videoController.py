from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

router = APIRouter(
    tags=["Vídeos"]
)

# ATENÇÃO: O caminho "/api-recordings" deve ser o caminho
# DENTRO do container da API que você mapeou no docker-compose.yml
# para o volume compartilhado.
#
# docker-compose.yml (exemplo):
#   volumes:
#     - recordings_volume:/api-recordings
#
router.mount(
    "/api/v1/videos", 
    StaticFiles(directory="/recordings", html=False), 
    name="videos"
)