import sys
import os
sys.path.append(os.getcwd())
# Mock ALL required env vars BEFORE importing settings
os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/db"
os.environ["MEDIA_MTX_HOST"] = "localhost"
os.environ["CONTROL_API_PORT"] = "9997"
os.environ["HLS_PORT"] = "8888"
os.environ["WEBRTC_PORT"] = "8889"
os.environ["MEDIAMTX_API_USER"] = "api-backend"
os.environ["MEDIAMTX_API_PASS"] = "UMA_SENHA_FORTE_E_SECRETA_AQUI"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

import httpx
import asyncio
import urllib.parse
from app.resources.settings.config import settings

# Mock Env
os.environ["MEDIAMTX_API_USER"] = "api-backend"
os.environ["MEDIAMTX_API_PASS"] = "UMA_SENHA_FORTE_E_SECRETA_AQUI"

USER = "api-backend"
PASS = "UMA_SENHA_FORTE_E_SECRETA_AQUI"
PATH_NAME = "live/test_patch"
ENCODED_PATH = urllib.parse.quote(PATH_NAME, safe='') # live%2Ftest_patch

async def test_patch():
    print(f"Testing PATCH {PATH_NAME} (encoded: {ENCODED_PATH})...")
    async with httpx.AsyncClient(auth=(USER, PASS), base_url="http://localhost:9997") as client:
        # 1. Try PATCH (Upsert)
        # Note: If path doesn't exist, PATCH returns 404 in my logic.
        # But here I just want to see if it BLOWS UP or returns 404 correctly.
        resp = await client.patch(f"/v3/config/paths/patch/{ENCODED_PATH}", json={"source": "publisher"})
        print(f"PATCH Response: {resp.status_code} - {resp.text}")
        
        if resp.status_code == 404:
            print("PATCH 404 (Expected if not exists). Slashes handled correctly?")
            # Proceed to ADD
            resp = await client.post(f"/v3/config/paths/add/{ENCODED_PATH}", json={"source": "publisher"})
            print(f"ADD Response: {resp.status_code} - {resp.text}")
        
        if resp.status_code == 200:
            print("Path Created!")
            # Now Try PATCH again to Update
            resp = await client.patch(f"/v3/config/paths/patch/{ENCODED_PATH}", json={"source": "publisher", "record": True})
            print(f"PATCH Update Response: {resp.status_code} - {resp.text}")
            
            # Cleanup
            resp = await client.delete(f"/v3/config/paths/delete/{ENCODED_PATH}")
            print(f"DELETE Response: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(test_patch())
