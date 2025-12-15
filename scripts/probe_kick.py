import httpx
import asyncio
import urllib.parse
import json

# SETTINGS
BASE_URL = "http://localhost:9997"
AUTH = ("api-backend", "UMA_SENHA_FORTE_E_SECRETA_AQUI")
PATH_NAME = "cam_repro"

async def probe_kick():
    async with httpx.AsyncClient(base_url=BASE_URL, auth=AUTH, timeout=10.0) as client:
        # 1. FIND ID
        print("--- Finding ID ---")
        list_res = await client.get("/v3/paths/list")
        if list_res.status_code != 200:
            print(f"List failed: {list_res.status_code}")
            return
            
        items = list_res.json().get('items', [])
        sid = None
        stype = None
        for item in items:
            if item['name'] == PATH_NAME:
                if item.get('source'):
                    sid = item['source'].get('id')
                    stype = item['source'].get('type')
                    print(f"Found Source: ID={sid}, Type={stype}")
                    break
        
        if not sid:
            print("No source found to kick.")
            return

        # 2. PROBE ENDPOINTS
        endpoints = [
            ("DELETE", f"/v3/rtspsessions/{sid}"),
            ("POST", f"/v3/rtspsessions/kick/{sid}"),
            ("DELETE", f"/v3/sessions/{sid}"),
            ("DELETE", f"/v3/clients/{sid}"),
            # Try previous ones just in case
            ("POST", f"/v3/clients/delete/{sid}"),
            ("DELETE", f"/v3/clients/delete/{sid}"),
        ]
        
        # If type is specifically rtspSession, prioritize that
        if stype == 'rtspSession':
             endpoints.insert(0, ("POST", f"/v3/rtspsessions/delete/{sid}")) # Try incorrect verb too?

        for method, url in endpoints:
            print(f"PROBING: {method} {url} ...")
            try:
                if method == "DELETE":
                    resp = await client.delete(url)
                else:
                    resp = await client.post(url)
                
                print(f"   -> SC: {resp.status_code} | Text: {resp.text}")
                
                if resp.status_code == 200:
                    print("   !!! SUCCESS !!!")
                    return
            except Exception as e:
                print(f"   -> Error: {e}")

if __name__ == "__main__":
    asyncio.run(probe_kick())
