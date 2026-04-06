"""Módulo de configuração de logging.

Este arquivo cria um logger compartilhado e exporta utilitários para outros
módulos da aplicação. A ideia é você ir adicionando logs gradualmente onde
fazer sentido. Não é necessário logar cada linha, apenas eventos importantes
(e.g. entrada/saída de endpoints, erros, decisões críticas).

Exemplos de uso:

    from app.resources.logging.logger import get_logger
    logger = get_logger(__name__)

    logger.info("Início do processamento")
    logger.debug(f"Payload recebido: {payload}")
    try:
        ...
    except Exception as e:
        logger.error("Falha ao processar", exc_info=True)
        raise

"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# diretório onde os logs serão gravados; crie se necessário
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# configuração básica; você pode mudar o formato ou nível conforme precisar
def setup_logging() -> None:
    """Configura o logger da aplicação. Chame no início, por exemplo em main.py."""
    root = logging.getLogger()  # logger raiz
    root.setLevel(logging.DEBUG)  # o nível mínimo que será capturado

    # handler para console (stderr)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)  # DEBUG vai para arquivo, INFO para console
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    root.addHandler(console)

    # handler rotativo para arquivo (roteina em 10MB, 5 backups)
    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s %(module)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger nomeado para uso em módulos."""
    return logging.getLogger(name)
