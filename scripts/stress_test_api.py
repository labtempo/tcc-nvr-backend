import asyncio
import httpx
import sys

# CONFIGURE
API_URL = "http://localhost:8000/api/v1"
LOGIN_URL = f"{API_URL}/login" # Changed from /auth/access-token
# Credentials
USERNAME = "tester@test.com" 
PASSWORD = "test"
CAMERA_NAME = "cam_stress"
RTSP_URL = "cam_stress" 

async def main():
    print(f"--- STRESS TEST API: {CAMERA_NAME} ---")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login
        print(f"[1] Logging in as {USERNAME}...")
        try:
             resp = await client.post(LOGIN_URL, json={"email": USERNAME, "password": PASSWORD})
             resp.raise_for_status()
             token = resp.json()["access_token"]
             print("    Login OK.")
        except Exception as e:
            print(f"!!! Login Failed: {e}") 
            print(f"    Response: {resp.text if 'resp' in locals() else 'No response'}")
            return

        headers = {"Authorization": f"Bearer {token}"}

        # 2. Cycle
        for i in range(1, 6):
            print(f"\n>>> CYCLE {i} <<<")
            
            # A. CREATE
            print("   [A] Creating Camera (Record=True)...")
            payload = {
                "name": CAMERA_NAME,
                "rtsp_url": RTSP_URL,
                "is_recording": True
            }
            try:
                resp = await client.post(f"{API_URL}/camera", json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    cam_id = data["id"]
                    print(f"       Success! ID={cam_id}")
                elif resp.status_code == 400 and "already registered" in resp.text:
                    # Clean up if exists from previous run
                     print("       Camera already exists in DB. Finding ID...")
                     # Get ID - Note: Endpoint for listing is /camera/user/{user_id} NOT /camera/
                     # We need user_id to find it. But we don't have user_id easily from Token login response?
                     # usersController /login returns user_id. We should capture it.
                     pass 
                else:
                    print(f"       Failed Create: {resp.status_code} - {resp.text}")
                    # Try to proceed? No.
                    continue
            except Exception as e:
                print(f"       Exception Create: {e}")
                continue

            # B. WAIT
            print("   [B] Waiting 3s...")
            await asyncio.sleep(3)

            # C. DELETE
            print(f"   [C] Deleting Camera {cam_id}...")
            try:
                resp = await client.delete(f"{API_URL}/camera/{cam_id}", headers=headers)
                if resp.status_code == 200:
                    print("       Delete OK.")
                else:
                    print(f"       Delete Failed: {resp.status_code} - {resp.text}")
            except Exception as e:
                print(f"       Exception Delete: {e}")

            # D. IMMEDIATE RE-CREATE (The Conflict Test)
            print("   [D] IMMEDIATE Re-Creating Camera...")
            try:
                resp = await client.post(f"{API_URL}/camera", json=payload, headers=headers)
                if resp.status_code == 200:
                    print("       !!! RE-CREATE SUCCESS !!!")
                    # Clean up for next cycle
                    new_id = resp.json()["id"]
                    await client.delete(f"{API_URL}/camera/{new_id}", headers=headers)
                    print("       (Cleaned up for next cycle)")
                else:
                    print(f"       !!! RE-CREATE FAILED: {resp.status_code} - {resp.text}")
            except Exception as e:
                 print(f"       Exception Re-Create: {e}")

if __name__ == "__main__":
    asyncio.run(main())
