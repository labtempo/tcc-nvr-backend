import os
# Set DB URL for localhost access (docker port 5433)
os.environ["DATABASE_URL"] = "postgresql://tcc_usr:tcc_pwd@localhost:5433/tcc_db"

from app.resources.database.connection import get_session
from app.domain.camera import Camera
from sqlmodel import select

def check_camera():
    session_gen = get_session()
    session = next(session_gen)
    
    statement = select(Camera).where(Camera.name == "test_cam_fixed")
    cam = session.exec(statement).first()
    
    if cam:
        print(f"SUCCESS: Camera found in DB! ID: {cam.id}, Name: {cam.name}, URL: {cam.rtsp_url}")
    else:
        print("FAILURE: Camera NOT found in DB.")

if __name__ == "__main__":
    check_camera()
