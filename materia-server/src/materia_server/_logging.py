import sys
from typing import Sequence
from loguru import logger
from loguru._logger import Logger
import logging
import inspect

from materia_server.config import Config


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = inspect.currentframe(), 2
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth = depth, exception = record.exc_info).log(level, record.getMessage())


def make_logger(config: Config, interceptions: Sequence[str] = ["uvicorn", "uvicorn.access", "uvicorn.error", "uvicorn.asgi", "fastapi"]) -> Logger:
    logger.remove() 

    if config.log.mode in ["console", "all"]:
        logger.add(
            sys.stdout, 
            enqueue = True, 
            backtrace = True,
            level = config.log.level.upper(), 
            format = config.log.console_format, 
            filter = lambda record: record["level"].name in ["INFO", "WARNING", "DEBUG", "TRACE"]
        )
        logger.add(
            sys.stderr, 
            enqueue = True, 
            backtrace = True,
            level = config.log.level.upper(), 
            format = config.log.console_format, 
            filter = lambda record: record["level"].name in ["ERROR", "CRITICAL"]
        )

    if config.log.mode in ["file", "all"]:
        logger.add(
            str(config.log.file),
            rotation = config.log.file_rotation,
            retention = config.log.file_retention, 
            enqueue = True, 
            backtrace = True, 
            level = config.log.level.upper(),
            format = config.log.file_format
        )

    logging.basicConfig(handlers = [InterceptHandler()], level = logging.NOTSET, force = True)

    for external_logger in interceptions:
        logging.getLogger(external_logger).handlers = [InterceptHandler()]

    return logger   # type: ignore

def uvicorn_log_config(config: Config) -> dict:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "default": {
                "class": "materia_server._logging.InterceptHandler"
            },
            "access": {
                "class": "materia_server._logging.InterceptHandler"
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": config.log.level.upper(), "propagate": False},
            "uvicorn.error": {"level": config.log.level.upper()},
            "uvicorn.access": {"handlers": ["access"], "level": config.log.level.upper(), "propagate": False},
        },
    }
