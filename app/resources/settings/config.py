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

settings = Settings()