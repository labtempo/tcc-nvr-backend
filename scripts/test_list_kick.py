
import httpx
import asyncio
import json

async def test_list_and_kick():
    list_url = "http://localhost:9997/v3/paths/list"
    auth = ("api-backend", "UMA_SENHA_FORTE_E_SECRETA_AQUI")
    
    print(f"Listing paths from {list_url}...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(list_url, auth=auth)
            print(f"List Status: {resp.status_code}")
            data = resp.json()
            print(json.dumps(data, indent=2))
            
            # Try to find teste
            for item in data.get('items', []):
                if item.get('name') == 'live/teste':
                    print("Found live/teste!")
                    source = item.get('source') # Check payload structure
                    print(f"Source: {source}")
                    if source and source.get('id'):
                        client_id = source.get('id')
                        print(f"Publisher ID: {client_id}. Kicking...")
                        kick_url = f"http://localhost:9997/v3/clients/delete/{client_id}" # Guessing endpoint
                        kresp = await client.post(kick_url, auth=auth)  # Assuming POST or DELETE? usually POST for actions
                        if kresp.status_code == 404: # Maybe DELETE method?
                             kresp = await client.delete(kick_url, auth=auth)
                        
                        print(f"Kick Status: {kresp.status_code}")
                        print(f"Kick Body: {kresp.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_list_and_kick())
