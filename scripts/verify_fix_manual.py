import httpx
import asyncio
import urllib.parse
import json
import time

# SETTINGS
BASE_URL = "http://localhost:9997"
AUTH = ("api-backend", "UMA_SENHA_FORTE_E_SECRETA_AQUI")
PATH_NAME = "cam8"
RTSP_URL = "publisher" 
RECORD = True

async def verify_fix():
    print(f"=== INICIANDO STRESS TEST PARA '{PATH_NAME}' ===")
    
    # URL Encode
    encoded_path_name = urllib.parse.quote(PATH_NAME, safe='')
    print(f"Encoded Path: {encoded_path_name}")
    
    add_endpoint = f"/v3/config/paths/add/{encoded_path_name}"
    patch_endpoint = f"/v3/config/paths/patch/{encoded_path_name}"
    delete_endpoint = f"/v3/config/paths/delete/{encoded_path_name}"
    
    async with httpx.AsyncClient(base_url=BASE_URL, auth=AUTH, timeout=10.0) as client:
        
        for i in range(1, 6):
            current_record = (i % 2 == 0) # Toggle record
            print(f"\n\n>>> ITERAÇÃO {i}: Definindo record={current_record}")
            
            payload = {
                "source": RTSP_URL,
                "record": current_record,
                "recordPath": "/recordings/%path/%Y-%m-%d_%H-%M-%S-%f",
                "recordFormat": "fmp4",
                "recordSegmentDuration": "10s",
                "recordDeleteAfter": "24h"
            }
            
            # --- Lógica do Controller/Service (Simplificada para Teste) ---
            success = False
            
            # 1. Tentar PATCH
            print(f"[1] Tentando PATCH...")
            try:
                resp = await client.patch(patch_endpoint, json=payload)
                if resp.status_code == 200:
                    print("SUCESSO: PATCH funcionou!")
                    success = True
                elif resp.status_code == 404:
                    print("PATCH 404. Tentando ADD...")
                else:
                    print(f"PATCH falhou: {resp.status_code}")
            except Exception as e:
                print(f"PATCH Ex: {e}")

            if not success:
                # 2. Loop Retry ADD
                print("[2] Tentando ADD com Retry...")
                for attempt in range(5):
                    # Blind Delete
                    try:
                        await client.post(delete_endpoint)
                    except: pass
                    
                    try:
                        resp = await client.post(add_endpoint, json=payload)
                        if resp.status_code == 200:
                            print(f"SUCESSO: ADD funcionou na tentativa {attempt+1}!")
                            success = True
                            break
                        
                        if resp.status_code == 400:
                            print(f"   ADD 400 (Already Exists). Kicking...")
                            # Kick Logic Replication
                            publisher_found = False
                            try:
                                list_res = await client.get("/v3/paths/list")
                                paths_data = list_res.json()
                                for item in paths_data.get('items', []):
                                    if item.get('name') == PATH_NAME:
                                        # DEBUG: Print item if suspicious
                                        if not item.get('source'):
                                            print(f"   [???] Ghost Item Found: {json.dumps(item)}")
                                        
                                        # Kick Source
                                        if item.get('source') and item['source'].get('id'):
                                            sid = item['source']['id']
                                            print(f"   Kick Source {sid}")
                                            await client.post(f"/v3/clients/delete/{sid}")
                                            publisher_found = True
                                        
                                        # Kick Readers
                                        for r in item.get('readers', []):
                                            rid = r.get('id')
                                            print(f"   Kick Reader {rid}")
                                            await client.post(f"/v3/clients/delete/{rid}")
                            except Exception as e:
                                print(f"Error fetching paths: {e}")
                            
                            wait = 0.5 if publisher_found else 1.0 # Simulate logic
                            print(f"   Aguardando {wait}s...")
                            await asyncio.sleep(wait)
                            continue
                            
                    except Exception as e:
                        print(f"   ADD Ex: {e}")
            
            if not success:
                print("!!! FALHA CRÍTICA NA ITERAÇÃO !!!")
                return

    print("\n\n=== STRESS TEST CONCLUÍDO COM SUCESSO ===")

if __name__ == "__main__":
    asyncio.run(verify_fix())
