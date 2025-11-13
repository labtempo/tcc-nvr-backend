import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    MEDIA_MTX_HOST: str
    CONTROL_API_PORT: str
    HLS_PORT: str
    WEBRTC_PORT: str
    MEDIAMTX_API_USER: str
    MEDIAMTX_API_PASS: str
    MEDIA_MTX_PLAYBACK_PORT: int = 9996
    PLAYBACK_TOKEN_SECRET_KEY: str = "3a9f4b2a8e1c7d6f5b9a2e8c1d7f6b5a4e3c2b1a0d9f8e7c6b5a4d3e2f1c0b9a" 
    PLAYBACK_TOKEN_ALGORITHM: str = "HS256"
    PLAYBACK_TOKEN_EXPIRE_SECONDS: int = 600

    @property
    def media_mtx_control_api_url(self) -> str:
        host = self.MEDIA_MTX_HOST.rstrip('/:')
        port = self.CONTROL_API_PORT.lstrip(':')
        return f"{host}:{port}"

    @property
    def media_mtx_hls_url(self) -> str:
        host = self.MEDIA_MTX_HOST.rstrip('/:')
        port = self.HLS_PORT.lstrip(':')
        return f"{host}:{port}"

    @property
    def media_mtx_playback_url(self) -> str:
        host = self.MEDIA_MTX_HOST.rstrip('/:')
        port = self.MEDIA_MTX_PLAYBACK_PORT
        return f"{host}:{port}"

settings = Settings()