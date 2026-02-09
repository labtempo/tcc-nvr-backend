
import httpx
import asyncio

async def test_kick():
    url = "http://mediamtx:9997/v3/paths/delete/live/cam6"
    auth = ("api-backend", "UMA_SENHA_FORTE_E_SECRETA_AQUI")
    
    print(f"Testing KICK on {url}...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, auth=auth)
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_kick())
