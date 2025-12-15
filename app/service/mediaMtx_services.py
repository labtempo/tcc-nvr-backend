# app/service/mediaMtx_services.py
import httpx
import asyncio
from app.resources.settings.config import settings
from typing import Dict, Any

class MediaMtxService:
    def __init__(self):
        auth = httpx.BasicAuth(settings.MEDIAMTX_API_USER, settings.MEDIAMTX_API_PASS)
        self.command_client = httpx.AsyncClient(
            base_url=settings.media_mtx_control_api_url,
            timeout=10.0,
            auth=auth
        )
        self.polling_client = httpx.AsyncClient(
            base_url=settings.media_mtx_control_api_url,
            timeout=30.0,
            auth=auth
        )

    async def create_and_verify_camera_path(self, path_name: str, rtsp_url: str) -> bool:
        add_endpoint = f"/v3/config/paths/add/{path_name}"
        get_endpoint = f"/v3/paths/get/{path_name}"
        delete_endpoint = f"/v3/config/paths/delete/{path_name}"

        try:
            await self.command_client.post(delete_endpoint)
            print(f"INFO: Path antigo '{path_name}' limpo com sucesso.")
        except httpx.HTTPStatusError:
            pass

        if rtsp_url.lower().startswith("publisher"):
            payload: Dict[str, Any] = {"source": "publisher", "record": True}
        else:
            payload = {"source": rtsp_url, "record": True}

        print(f"INFO: Enviando comando de criação para o path '{path_name}' com payload: {payload}")
        try:
            response_add = await self.command_client.post(add_endpoint, json=payload)
            response_add.raise_for_status()
            print(f"SUCESSO: Comando para criar '{path_name}' foi aceito pelo MediaMTX.")
        except httpx.RequestError as e:
            raise Exception(f"Falha de comunicação ao criar path no MediaMTX: {e}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"MediaMTX rejeitou a criação do path '{path_name}': {e.response.status_code} - {e.response.text}")

        max_retries = 10
        delay = 0.5
        print(f"INFO: Iniciando verificação de prontidão para o path '{path_name}'...")
        for i in range(max_retries):
            try:
                response_get = await self.polling_client.get(get_endpoint)
                if response_get.status_code == 200:
                    print(f"SUCESSO: Path '{path_name}' está ativo e pronto para conexão!")
                    return True
            except httpx.RequestError as e:
                raise Exception(f"Falha de comunicação durante o polling do MediaMTX: {e}")
            
            print(f"INFO: Tentativa {i+1}/{max_retries}. Path '{path_name}' ainda não está pronto. Aguardando {delay}s...")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 5)

        raise TimeoutError(f"O path '{path_name}' não ficou pronto no MediaMTX a tempo.")

    async def create_camera_path(self, path_name: str, rtsp_url: str):
        """Create a camera path in MediaMTX"""
        add_endpoint = f"/v3/config/paths/add/{path_name}"
        
        if rtsp_url.lower().startswith("publisher"):
            payload: Dict[str, Any] = {"source": "publisher", "record": True}
        else:
            payload = {"source": rtsp_url, "record": True}

        try:
            response = await self.command_client.post(add_endpoint, json=payload)
            response.raise_for_status()
        except httpx.RequestError as e:
            raise Exception(f"Falha de comunicação ao criar path no MediaMTX: {e}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"MediaMTX rejeitou a criação do path '{path_name}': {e.response.status_code} - {e.response.text}")

    async def delete_camera_path(self, path_name: str):
        """Delete a camera path in MediaMTX"""
        delete_endpoint = f"/v3/config/paths/delete/{path_name}"
        try:
            response = await self.command_client.post(delete_endpoint)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"INFO: Path '{path_name}' já não existia no MediaMTX.")
            else:
                raise Exception(f"MediaMTX falhou ao deletar path '{path_name}': {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
             raise Exception(f"Falha de comunicação ao deletar path no MediaMTX: {e}")
media_mtx_service = MediaMtxService()