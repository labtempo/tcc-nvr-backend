from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class Record(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    camera_id: int = Field(foreign_key="camera.id")
    nome_arquivo: str
    url_acesso: str
    duracao_segundos: int
    data_criacao: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))
    data_inicio_segmento: datetime
    data_fim_segmento: datetime