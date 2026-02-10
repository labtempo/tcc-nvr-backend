import httpx
import asyncio
import urllib.parse

async def test_delete():
    base_url = "http://localhost:9997"
    path_name = "live/teste"
    auth = ("api-backend", "UMA_SENHA_FORTE_E_SECRETA_AQUI")
    
    encoded_path = urllib.parse.quote(path_name, safe='')
    
    print(f"Testing deletion for '{path_name}'...")
    print(f"Encoded: '{encoded_path}'")
    
    endpoints = [
        f"/v3/config/paths/delete/{path_name}",
        f"/v3/config/paths/delete/{encoded_path}"
    ]
    
    async with httpx.AsyncClient() as client:
        # Check if it exists first
        print("Checking if path exists...")
        list_url = f"{base_url}/v3/paths/list"
        resp = await client.get(list_url, auth=auth)
        data = resp.json()
        found = False
        for item in data.get('items', []):
            if item.get('name') == path_name:
                print(f"Found '{path_name}' in list!")
                found = True
        
        if not found:
            print(f"Warning: '{path_name}' not found in list, delete might fail anyway.")

        for ep in endpoints:
            url = f"{base_url}{ep}"
            print(f"Trying DELETE endpoint: {url}")
            try:
                # Try POST (as typically used in this app)
                resp = await client.post(url, auth=auth)
                print(f"POST Status: {resp.status_code}")
                if resp.status_code != 200:
                    print(f"Body: {resp.text}")
                
                # Try DELETE verb just in case
                if resp.status_code == 404:
                     print("Trying DELETE verb...")
                     resp = await client.delete(url, auth=auth)
                     print(f"DELETE Status: {resp.status_code}")

            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_delete())
