
from datetime import datetime
import re
from datetime import timedelta

class WebhookService:
    @property
    def nome_arquivo(self) -> str:
        return self.absolute_path.split('/')[-1]

    @property
    def duracao_segundos(self) -> int:
        return int(self.duration_ns / 1_000_000_000)

    @property
    def data_inicio_segmento(self) -> datetime.datetime:
        # Regex para achar o timestamp no nome do arquivo
        match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', self.absolute_path)
        if match:
            timestamp_str = match.group(1)
            try:
                return datetime.datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
            except ValueError:
                pass  
        return datetime.datetime.now() - timedelta(seconds=self.duracao_segundos)

    @property
    def data_fim_segmento(self) -> datetime.datetime:
        return self.data_inicio_segmento + timedelta(seconds=self.duracao_segundos)