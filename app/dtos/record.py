from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RecordCreate(BaseModel):
    camera_id: int
    nome_arquivo: str
    duracao_segundos: int
    data_inicio_segmento: datetime
    data_fim_segmento: datetime

class RecordData(BaseModel):
    id: int
    camera_id: int
    nome_arquivo: str
    url_acesso: str
    duracao_segundos: int
    data_criacao: datetime
    data_inicio_segmento: datetime
    data_fim_segmento: datetime