import httpx
import asyncio
import json

async def deep_inspect():
    base_url = "http://localhost:9997"
    auth = ("api-backend", "UMA_SENHA_FORTE_E_SECRETA_AQUI")
    target = "live/cam8"
    
    async with httpx.AsyncClient(base_url=base_url, auth=auth) as client:
        print(f"--- INSPECTING '{target}' ---")
        
        # 1. PATHS List (Active)
        try:
            resp = await client.get("/v3/paths/list")
            data = resp.json()
            found = False
            for item in data.get('items', []):
                if item.get('name') == target:
                    print("FOUND IN ACTIVE PATHS:")
                    print(json.dumps(item, indent=2))
                    found = True
            if not found:
                print("NOT FOUND in Active Paths.")
        except Exception as e:
            print(f"Error paths: {e}")

        # 2. CONFIG List
        try:
            resp = await client.get("/v3/config/paths/list")
            data = resp.json()
            found = False
            for item in data.get('items', []):
                if item.get('name') == target:
                    print("FOUND IN CONFIG PATHS:")
                    print(json.dumps(item, indent=2))
                    found = True
            if not found:
                print("NOT FOUND in Config Paths.")
        except Exception as e:
            print(f"Error config: {e}")

if __name__ == "__main__":
    asyncio.run(deep_inspect())
