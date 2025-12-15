import httpx
import asyncio
import os
import urllib.parse
from app.resources.settings.config import settings

# Mock Env
os.environ["MEDIAMTX_API_USER"] = "api-backend"
os.environ["MEDIAMTX_API_PASS"] = "UMA_SENHA_FORTE_E_SECRETA_AQUI"

USER = "api-backend"
PASS = "UMA_SENHA_FORTE_E_SECRETA_AQUI"
PATH_NAME = "cam_stress"
ENCODED_PATH = urllib.parse.quote(PATH_NAME, safe='')

async def test_add():
    print(f"Testing ADD {PATH_NAME} (source=publisher)...")
    async with httpx.AsyncClient(auth=(USER, PASS), base_url="http://localhost:9997") as client:
        # 1. Check if exists
        resp = await client.get("/v3/paths/list")
        exists = False
        if resp.status_code == 200:
            for item in resp.json().get('items', []):
                if item['name'] == PATH_NAME:
                    print(f"Path exists: {item}")
                    exists = True
                    break
        
        # 2. Try ADD (mocking the service logic manually to see raw errors)
        # But actually I want to test the SERVICE logic.
        # So I should import the service.
        pass

if __name__ == "__main__":
    from app.service.mediaMtx_services import media_mtx_service
    try:
        asyncio.run(media_mtx_service.create_and_verify_camera_path(PATH_NAME, "publisher", True))
        print("SUCCESS")
    except Exception as e:
        print(f"FAILED: {e}")
