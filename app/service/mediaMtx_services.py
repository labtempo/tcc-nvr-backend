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

    def _get_kick_endpoint(self, session_type: str, session_id: str) -> str:
        # Standard MediaMTX v3 pluralization
        type_map = {
            "rtspSession": "rtspsessions",
            "rtspsession": "rtspsessions",
            "rtmpSession": "rtmpsessions",
            "rtmpsession": "rtmpsessions",
            "hlsSession": "hlssessions",
            "hlssession": "hlssessions",
            "webrtcSession": "webrtcsessions",
            "webrtcsession": "webrtcsessions",
            "srtSession": "srtsessions",
            "srtsession": "srtsessions",
        }
        resource = type_map.get(session_type, "sessions") # Fallback
        return f"/v3/{resource}/kick/{session_id}"

    async def create_and_verify_camera_path(self, path_name: str, rtsp_url: str, record: bool = False) -> bool:
        import urllib.parse
        encoded_path_name = urllib.parse.quote(path_name, safe='')
        
        add_endpoint = f"/v3/config/paths/add/{encoded_path_name}"
        patch_endpoint = f"/v3/config/paths/patch/{encoded_path_name}"  # Added
        get_endpoint = f"/v3/paths/get/{encoded_path_name}"
        delete_endpoint = f"/v3/config/paths/delete/{encoded_path_name}"

        # Tentar limpar path antigo se existir (Blind Delete)
        # REMOVED Blind Delete from here - we want to try PATCH first
        
        if rtsp_url.lower().startswith("publisher"):
            payload: Dict[str, Any] = {"source": "publisher"}
        else:
            payload = {"source": rtsp_url}
        
        payload["record"] = record
        if record:
             payload["recordPath"] = "/recordings/%path/%Y-%m-%d_%H-%M-%S-%f"
             payload["recordFormat"] = "fmp4"
             payload["recordSegmentDuration"] = "10s"
             payload["recordDeleteAfter"] = "24h"

        print(f"INFO: Enviando comando de criação (PATCH/ADD) para o path '{path_name}' com payload: {payload}")

        # 1. Tentar Atualizar (PATCH) - Atomic Update / Upsert se já existir
        try:
            print(f"INFO: Tentando assumir path '{path_name}' via PATCH...")
            response = await self.command_client.patch(patch_endpoint, json=payload)
            if response.status_code == 200:
                print(f"SUCESSO: Path '{path_name}' existente foi atualizado/assumido via PATCH.")
                # Se sucesso, pulamos direto para a verificação
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

            elif response.status_code != 404:
                 # Erro real (ex: 400 Bad Request que não seja 'Not Found')
                 print(f"INFO: PATCH falhou com {response.status_code}, tentando ADD...")
            else:
                 print(f"INFO: Path '{path_name}' não existe (404), prosseguindo para ADD...")
        except httpx.RequestError as e:
             print(f"WARN: Falha no PATCH ({e}), tentando ADD...")

        # 2. Se PATCH falhou (404 ou erro), tentamos ADD com Retry Loop
        # Blind delete antes de tentar criar novo
        try:
            await self.command_client.post(delete_endpoint)
        except (httpx.RequestError, httpx.HTTPStatusError):
            pass
        
        # Lógica de Retry com Kick
        last_error = None
        for attempt in range(20):
             try:
                response_add = await self.command_client.post(add_endpoint, json=payload)
                response_add.raise_for_status()
                print(f"SUCESSO: Comando para criar '{path_name}' foi aceito pelo MediaMTX.")
                break # Sucesso
             except httpx.HTTPStatusError as e:
                last_error = e
                print(f"DEBUG: Erro {e.response.status_code} ao criar path. Body: {e.response.text}")
                
                # Se for 400, assumimos que pode ser conflito com publisher existente ou configuração.
                # Tentamos verificar se existe publisher para chutar.
                if e.response.status_code == 400:
                    print(f"AVISO: Possível conflito no ADD '{path_name}' (tentativa {attempt+1}). Verificando publishers...")
                    
                    # Kick Logic
                    publisher_found = False
                    try:
                        list_res = await self.polling_client.get("/v3/paths/list")
                        if list_res.status_code == 200:
                            paths_data = list_res.json()
                            for item in paths_data.get('items', []):
                                if item.get('name') == path_name:
                                    # 1. Kick Publisher
                                    source = item.get('source')
                                    if source and source.get('id'):
                                        client_id = source.get('id')
                                        stype = source.get('type', 'rtspSession')
                                        print(f"INFO: Encontrado publisher conflitante (ID {client_id}, Type {stype}). Tentando desconectar...")
                                        publisher_found = True
                                        
                                        kick_endpoint = self._get_kick_endpoint(stype, client_id)
                                        try:
                                             await self.command_client.post(kick_endpoint)
                                        except httpx.HTTPStatusError as kick_err:
                                             print(f"WARN: Falha ao chutar publisher: {kick_err}")
                                    
                                    # 2. Kick Readers (Visualizadores)
                                    readers = item.get('readers', [])
                                    if readers:
                                        print(f"INFO: Encontrados {len(readers)} leitores ativos no path. Tentando desconectar...")
                                        for reader in readers:
                                            reader_id = reader.get('id')
                                            stype = reader.get('type', 'rtspSession')
                                            if reader_id:
                                                kick_endpoint = self._get_kick_endpoint(stype, reader_id)
                                                try:
                                                    await self.command_client.post(kick_endpoint)
                                                except httpx.HTTPStatusError:
                                                     pass

                                    break # Apenas um por path
                    except Exception as k_err:
                        print(f"ERRO ao tentar chutar cliente: {k_err}")
                    
                    # Reforçar a exclusão da configuração antiga se existir
                    try:
                        await self.command_client.post(delete_endpoint)
                    except (httpx.RequestError, httpx.HTTPStatusError):
                        pass

                    wait_time = 0.5 if publisher_found else 1.0
                    print(f"INFO: Aguardando {wait_time}s antes de retentar (Tentativa {attempt+1}/20)...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                     raise Exception(f"MediaMTX rejeitou a criação do path '{path_name}': {e.response.status_code} - {e.response.text}")
             except httpx.RequestError as e:
                 raise Exception(f"Falha de comunicação ao criar path no MediaMTX: {e}")
        
        if last_error and attempt == 19: 
             raise Exception(f"Falha ao criar path '{path_name}' após retentativas: {last_error.response.text}")

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

    async def create_camera_path(self, path_name: str, rtsp_url: str, record: bool = False):
        """Create or update a camera path in MediaMTX."""
        # Encode path name to handle slashes correctly in URL
        import urllib.parse
        encoded_path_name = urllib.parse.quote(path_name, safe='')
        
        add_endpoint = f"/v3/config/paths/add/{encoded_path_name}"
        patch_endpoint = f"/v3/config/paths/patch/{encoded_path_name}"
        delete_endpoint = f"/v3/config/paths/delete/{encoded_path_name}"

        # Setup Payload
        if rtsp_url.lower().startswith("publisher"):
            payload: Dict[str, Any] = {"source": "publisher"}
        else:
            payload = {"source": rtsp_url}

        payload["record"] = record
        if record:
             payload["recordPath"] = "/recordings/%path/%Y-%m-%d_%H-%M-%S-%f"
             payload["recordFormat"] = "fmp4"
             payload["recordSegmentDuration"] = "10s"
             payload["recordDeleteAfter"] = "24h"

        # 1. Tentar Atualizar (PATCH) - Atomic Update
        try:
            print(f"INFO: Tentando atualizar path '{path_name}' via PATCH...")
            response = await self.command_client.patch(patch_endpoint, json=payload)
            if response.status_code == 200:
                print(f"SUCESSO: Path '{path_name}' atualizado via PATCH.")
                return
            elif response.status_code != 404:
                # Se der erro que não seja 404 (Path não encontrado), levantamos exceção
                raise Exception(f"Erro no PATCH: {response.status_code} - {response.text}")
            
            print(f"INFO: Path '{path_name}' não existe (404), tentando criar via ADD...")
        except httpx.RequestError as e:
             raise Exception(f"Falha de comunicação no PATCH: {e}")

        # 2. Se PATCH falhou com 404, tentamos ADD (com lógica de retry e KICK)
        last_error = None
        for attempt in range(20):
            # Tentar Deletar (Blind Delete inicial)
            try:
                await self.command_client.post(delete_endpoint)
            except (httpx.RequestError, httpx.HTTPStatusError):
                pass 
            
            await asyncio.sleep(0.5)

            try:
                response = await self.command_client.post(add_endpoint, json=payload)
                response.raise_for_status()
                print(f"SUCESSO: Path '{path_name}' criado via ADD.")
                return
            except httpx.HTTPStatusError as e:
                last_error = e
                print(f"DEBUG: Erro {e.response.status_code} ao criar path. Body: {e.response.text}")
                
                # Se for 400, assumimos que pode ser conflito com publisher existente ou configuração.
                if e.response.status_code == 400:
                    print(f"AVISO: Possível conflito no ADD '{path_name}' (tentativa {attempt+1}). Verificando publishers...")
                    
                    # Kick Logic
                    publisher_found = False
                    try:
                        list_res = await self.polling_client.get("/v3/paths/list")
                        if list_res.status_code == 200:
                            paths_data = list_res.json()
                            for item in paths_data.get('items', []):
                                if item.get('name') == path_name:
                                    # 1. Kick Publisher
                                    source = item.get('source')
                                    if source and source.get('id'):
                                        client_id = source.get('id')
                                        stype = source.get('type', 'rtspSession')
                                        print(f"INFO: Encontrado publisher conflitante (ID {client_id}, Type {stype}). Tentando desconectar...")
                                        publisher_found = True
                                        
                                        kick_endpoint = self._get_kick_endpoint(stype, client_id)
                                        try:
                                             await self.command_client.post(kick_endpoint)
                                        except httpx.HTTPStatusError as kick_err:
                                             print(f"WARN: Falha ao chutar publisher: {kick_err}")
                                    
                                    # 2. Kick Readers (Visualizadores)
                                    readers = item.get('readers', [])
                                    if readers:
                                        print(f"INFO: Encontrados {len(readers)} leitores ativos no path. Tentando desconectar...")
                                        for reader in readers:
                                            reader_id = reader.get('id')
                                            stype = reader.get('type', 'rtspSession')
                                            if reader_id:
                                                kick_endpoint = self._get_kick_endpoint(stype, reader_id)
                                                try:
                                                    await self.command_client.post(kick_endpoint)
                                                except httpx.HTTPStatusError:
                                                     pass

                                    break # Apenas um publisher por path normalmente
                    except Exception as k_err:
                        print(f"ERRO ao tentar chutar cliente: {k_err}")
                    
                    # Reforçar a exclusão da configuração antiga se existir
                    try:
                        await self.command_client.post(delete_endpoint)
                    except (httpx.RequestError, httpx.HTTPStatusError):
                        pass

                    wait_time = 0.5 if publisher_found else 1.0
                    print(f"INFO: Aguardando {wait_time}s antes de retentar (Tentativa {attempt+1}/20)...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"MediaMTX rejeitou ADD '{path_name}': {e.response.text}")
            except httpx.RequestError as e:
                raise Exception(f"Falha de comunicação no ADD: {e}")

        if last_error: # No create_camera_path this implicitly handles return/exception
             raise Exception(f"Falha ao criar path '{path_name}' após retentativas: {last_error.response.text}")
        raise Exception(f"Falha ao criar path '{path_name}'.")

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