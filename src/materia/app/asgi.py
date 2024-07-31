from os import environ
from pathlib import Path
from uvicorn.workers import UvicornWorker
from materia.config import Config
from materia._logging import uvicorn_log_config


class MateriaWorker(UvicornWorker):
    CONFIG_KWARGS = {
        "loop": "uvloop",
        "log_config": uvicorn_log_config(Config.open(Path(environ["MATERIA_CONFIG"]).resolve()))
    }
