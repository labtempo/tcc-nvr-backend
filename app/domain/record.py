import re
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

class MediaMTXWebhookPayload(BaseModel):
    stream_path: str = Field(alias="path")
    absolute_path: str = Field(alias="absolutePath")
    duration_ns: int = Field(alias="duration")  

    @property
    def nome_arquivo(self) -> str:
        """Extrai o nome do arquivo do caminho absoluto."""
        return self.absolute_path.split('/')[-1]

    @property
    def duracao_segundos(self) -> int:
        """Converte nanossegundos para segundos."""
        return int(self.duration_ns / 1_000_000_000)

    @property
    def data_inicio_segmento(self) -> datetime:
        """
        Extrai a data de início do nome do arquivo.
        Baseado no formato: ...%path-%Y-%m-%d_%H-%M-%S
        Ex: /recordings/live_obs_publisher-2025-10-27_18-30-00.mp4
        """
        match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', self.absolute_path)
        if match:
            timestamp_str = match.group(1)
            try:
                return datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
            except ValueError:
                pass 
        
        return datetime.now() - timedelta(seconds=self.duracao_segundos)

    @property
    def data_fim_segmento(self) -> datetime:
        """Calcula a data de fim baseado no início e duração."""
        return self.data_inicio_segmento + timedelta(seconds=self.duracao_segundos)