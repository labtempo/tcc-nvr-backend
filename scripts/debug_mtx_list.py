import httpx
import asyncio
import json
import os

# Mock like create_test_user
os.environ["MEDIAMTX_API_USER"] = "user" # Dummy
os.environ["MEDIAMTX_API_PASS"] = "pass"
# But we need real creds for MediaMTX? 
# docker-compose says: MEDIAMTX_API_USER: 'api-backend', MEDIAMTX_API_PASS: 'UMA_SENHA_FORTE_E_SECRETA_AQUI'
# I must use THOSE.

USER = "api-backend"
PASS = "UMA_SENHA_FORTE_E_SECRETA_AQUI"
URL = "http://localhost:9997/v3/paths/list"

async def main():
    async with httpx.AsyncClient(auth=(USER, PASS)) as client:
        print("--- CONFIG PATHS ---")
        try:
            resp = await client.get("http://localhost:9997/v3/config/paths/list")
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print(json.dumps(resp.json(), indent=2))
            else:
                print(resp.text)
        except Exception as e:
            print(e)
            
        print("\n--- RUNTIME PATH DETAILS (cam_stress) ---")
        try:
            resp = await client.get("http://localhost:9997/v3/paths/get/cam_stress")
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print(json.dumps(resp.json(), indent=2))
            else:
                print(resp.text)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    asyncio.run(main())
