import httpx
import asyncio
import json

async def list_configs():
    base_url = "http://localhost:9997"
    url = f"{base_url}/v3/config/paths/list"
    auth = ("api-backend", "UMA_SENHA_FORTE_E_SECRETA_AQUI")
    
    print(f"Fetching config list from {url}...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, auth=auth)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(json.dumps(data, indent=2))
            else:
                print(f"Error Body: {resp.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_configs())
