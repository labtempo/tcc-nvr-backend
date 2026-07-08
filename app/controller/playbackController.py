from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
import httpx
from app.resources.settings.config import settings 

router = APIRouter()

@router.get("/playback/video")
async def stream_playback(
    path: str = Query(...),
    start: str = Query(...),
    duration: float = Query(...)
):
    # Validar formato RFC3339 para o timestamp 'start'
    import re
    rfc3339_regex = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})$"
    if not re.match(rfc3339_regex, start):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O parâmetro 'start' deve estar no formato RFC3339 estrito (ex: YYYY-MM-DDTHH:MM:SSZ)"
        )

    # 1. Tratamento da Duração
    duration_int = int(duration)

    # 2. Configurar MediaMTX
    mediamtx_url = f"{settings.media_mtx_playback_url}/{path}/get"
    auth = (settings.MEDIAMTX_API_USER, settings.MEDIAMTX_API_PASS)
    params = {"start": start, "duration": duration_int, "format": "mp4"}

    # 3. Iniciar Cliente HTTP com timeout específico para processamento longo
    timeout_config = httpx.Timeout(connect=15.0, read=None, write=15.0, pool=None)
    client = httpx.AsyncClient(auth=auth, timeout=timeout_config)
    
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
        # Função geradora assíncrona para ler os bytes do MediaMTX com segurança
        async def generate_video_stream():
            try:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    yield chunk
            except Exception:
                # Captura se o navegador/cliente fechar a aba ou cancelar no meio
                import logging
                logging.getLogger("uvicorn").info("Conexão de streaming abortada pelo cliente.")
                raise
            finally:
                await response.aclose()
                await client.aclose()

        # Retornar o Stream usando o gerador seguro
        return StreamingResponse(
            generate_video_stream(), 
            status_code=200,
            media_type="video/mp4"
        )
    
    except httpx.ConnectError:
        await client.aclose() # Garante fechamento em caso de erro
        raise HTTPException(status_code=503, detail="Servidor de mídia indisponível")
