import sys
import os
sys.path.append(os.getcwd())
# Force DATABASE_URL
os.environ["DATABASE_URL"] = "postgresql://tcc_usr:tcc_pwd@localhost:5433/tcc_db"

from app.resources.database.connection import engine
from sqlmodel import Session, select
from app.domain.camera import Camera

def cleanup():
    print("Cleaning up cam_stress...")
    with Session(engine) as session:
        statement = select(Camera).where(Camera.name == "cam_stress")
        existing = session.exec(statement).first()
        if existing:
            session.delete(existing)
            session.commit()
            print("Deleted cam_stress.")
        else:
            print("cam_stress not found.")

if __name__ == "__main__":
    cleanup()
