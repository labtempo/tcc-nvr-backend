import httpx
import asyncio
import urllib.parse
import json
import time
import subprocess
import threading

# SETTINGS
BASE_URL = "http://localhost:9997"
AUTH = ("api-backend", "UMA_SENHA_FORTE_E_SECRETA_AQUI")
PATH_NAME = "cam_repro"
# We use the same docker command the user uses, but targeting cam_repro
DOCKER_CMD = [
    "docker", "run", "--rm", "-i", 
    "jrottenberg/ffmpeg:4.1-alpine", 
    "-re", 
    "-f", "lavfi", "-i", "testsrc=size=1280x720:rate=30", 
    "-c:v", "libx264", 
    "-pix_fmt", "yuv420p", 
    "-preset", "ultrafast", 
    "-tune", "zerolatency", 
    "-f", "rtsp", 
    "-rtsp_transport", "tcp", 
    f"rtsp://host.docker.internal:8554/{PATH_NAME}"
]

stop_publisher = False

def publisher_loop():
    while not stop_publisher:
        print(f"[Publisher] Starting FFMPEG for {PATH_NAME}...")
        try:
            # Run roughly for 30s or until killed
            proc = subprocess.Popen(DOCKER_CMD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            while proc.poll() is None and not stop_publisher:
                time.sleep(0.5)
            
            if stop_publisher:
                proc.terminate()
                print("[Publisher] Stopping...")
                return
            
            # If it died naturally or was kicked, wait 2s (like the user script) and restart
            print("[Publisher] FFMPEG died. Restarting in 2s...")
            time.sleep(2)
        except Exception as e:
            print(f"[Publisher] Error: {e}")
            time.sleep(2)

async def run_cycle():
    client = httpx.AsyncClient(base_url=BASE_URL, auth=AUTH, timeout=10.0)
    
    encoded_path = urllib.parse.quote(PATH_NAME, safe='')
    add_url = f"/v3/config/paths/add/{encoded_path}"
    del_url = f"/v3/config/paths/delete/{encoded_path}"
    
    payload = {
        "source": "publisher",
        "record": True,
        "recordPath": "/recordings/%path/%Y-%m-%d_%H-%M-%S-%f",
        "recordFormat": "fmp4",
        "recordSegmentDuration": "10s",
        "recordDeleteAfter": "24h"
    }

    print("--- CYCLE START ---")
    
    # 1. Create (Initial)
    print("[Action] Creating Config...")
    try:
        await client.post(add_url, json=payload)
        print("   Create OK.")
    except Exception as e:
        print(f"   Create Failed: {e}")

    await asyncio.sleep(5)  # Let it stabilize and recording start

    # 2. Delete (User deletes via UI)
    print("[Action] Deleting Config...")
    try:
        await client.post(del_url)
        print("   Delete OK.")
    except Exception as e:
        print(f"   Delete Failed: {e}")
        
    print("[State] Config deleted. Publisher should still be active (or reconnecting).")
    await asyncio.sleep(3) # Wait a bit to ensure publisher is in specific state (either connected to empty path or reconnecting)

    # 3. Re-Create (User adds again)
    print("[Action] Re-Creating Config (Expect Conflict)...")
    
    # Simulate the SERVICE Logic (Retry Loop)
    success = False
    for i in range(5):
        print(f"   Attempt {i+1}...")
        try:
            # Blind Delete logic from service
            try: await client.post(del_url) 
            except: pass

            resp = await client.post(add_url, json=payload)
            if resp.status_code == 200:
                print("   SUCCESS: Re-created config!")
                success = True
                break
            
            if resp.status_code == 400:
                print("   Got 400. Analyzing Conflict...")
                # Inspect Item
                list_res = await client.get("/v3/paths/list")
                items = list_res.json().get('items', [])
                found = False
                for item in items:
                    if item['name'] == PATH_NAME:
                        found = True
                        print(f"   [Conflict Item] {json.dumps(item)}")
                        
                        # KICK LOGIC
                        if item.get('source') and item['source'].get('id'):
                            sid = item['source']['id']
                            print(f"   [KICK] kicking source {sid}")
                            kr = await client.post(f"/v3/rtspsessions/kick/{sid}")
                            print(f"   [KICK RESP] {kr.status_code} - {kr.text}")
                            found_publisher = True
                        else:
                            print("   [KICK] No source ID found!")
                            found_publisher = False
                        
                        wait = 0.2 if found_publisher else 1.0
                        print(f"   Waiting {wait}s...")
                        await asyncio.sleep(wait)
                        
                if not found:
                    print("   [Conflict] 400 returned but path NOT found in list?")
                    await asyncio.sleep(1)
        
        except Exception as e:
            print(f"   Error: {e}")
            await asyncio.sleep(1)
            
    if not success:
        print("!!! TEST FAILED: Could not re-create config.")
    else:
        print("TEST PASSED.")

    global stop_publisher
    stop_publisher = True

if __name__ == "__main__":
    # Start fake publisher
    t = threading.Thread(target=publisher_loop)
    t.start()
    
    time.sleep(2) # Wait for publisher to start
    
    try:
        asyncio.run(run_cycle())
    finally:
        stop_publisher = True
        t.join()
