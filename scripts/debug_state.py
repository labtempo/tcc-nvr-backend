import httpx
import asyncio
import json

async def debug_state():
    base_url = "http://localhost:9997"
    auth = ("api-backend", "UMA_SENHA_FORTE_E_SECRETA_AQUI")
    
    async with httpx.AsyncClient() as client:
        print("=== CONFIGURED PATHS (from /v3/config/paths/list) ===")
        try:
            resp = await client.get(f"{base_url}/v3/config/paths/list", auth=auth)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get('items', []):
                    print(f"Name: '{item.get('name')}' | Source: {item.get('source')}")
            else:
                print(f"Error fetching configs: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"Ex: {e}")

        print("\n=== ACTIVE PATHS (from /v3/paths/list) ===")
        try:
            resp = await client.get(f"{base_url}/v3/paths/list", auth=auth)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get('items', []):
                    name = item.get('name')
                    confName = item.get('confName')
                    source = item.get('source')
                    readers = item.get('readers', [])
                    print(f"Name: '{name}' | ConfName: '{confName}' | Source: {source} | Readers: {len(readers)}")
            else:
                print(f"Error fetching paths: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"Ex: {e}")

if __name__ == "__main__":
    asyncio.run(debug_state())
