from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
import httpx
from app.security.security import decode_temp_playback_token
from app.resources.settings.config import settings 
from starlette.background import BackgroundTask

router = APIRouter()

@router.get("/playback/video")
async def stream_playback(token: str = Query(...)):
    # 1. Validar Token
    try:
        payload = decode_temp_playback_token(token)
        path = payload.get("path")
        start = payload.get("start")
        duration = payload.get("duration")
        
        if not all([path, start, duration]):
            raise HTTPException(status_code=400, detail="Token inválido")
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

    # 2. Configurar MediaMTX
    mediamtx_url = f"{settings.media_mtx_playback_url}/get"
    auth = (settings.MEDIAMTX_API_USER, settings.MEDIAMTX_API_PASS)
    params = {"path": path, "start": start, "duration": duration, "format": "mp4"}

    # 3. Iniciar Cliente HTTP
    client = httpx.AsyncClient(auth=auth)
    
    try:
        # Usamos build_request + send para ter controle manual do stream
        req = client.build_request("GET", mediamtx_url, params=params)
        response = await client.send(req, stream=True)
        
        # Se o MediaMTX rejeitar (ex: 404 ou 401), fechamos tudo e avisamos
        if response.status_code != 200:
            await response.aclose()
            await client.aclose()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, 
                detail=f"Erro no MediaMTX: {response.status_code}"
            )

        # Função para limpar a memória quando o vídeo terminar
        async def cleanup():
            await response.aclose()
            await client.aclose()

        # 4. Retornar o Stream
        return StreamingResponse(
            response.aiter_bytes(), 
            status_code=200,
            media_type="video/mp4",
            background=BackgroundTask(cleanup) # Fecha conexão ao terminar
        )
    
    except httpx.ConnectError:
        await client.aclose() # Garante fechamento em caso de erro
        raise HTTPException(status_code=503, detail="Servidor de mídia indisponível")
