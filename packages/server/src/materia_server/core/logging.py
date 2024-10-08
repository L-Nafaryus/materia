import sys
from typing import Sequence, Literal, Optional, TypeAlias
from pathlib import Path
from loguru import logger
from loguru._logger import Logger as LoggerInstance
import logging
import inspect


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

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


LogLevel: TypeAlias = Literal["info", "warning", "error", "critical", "debug", "trace"]
LogMode: TypeAlias = Literal["console", "file", "all"]


class Logger:
    __instance__: Optional[LoggerInstance] = None

    def __init__(self):
        raise NotImplementedError()

    @staticmethod
    def new(
        mode: LogMode = "console",
        level: LogLevel = "info",
        console_format: str = (
            "<level>{level: <8}</level> <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> - {message}"
        ),
        file_format: str = (
            "<level>{level: <8}</level>: <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> - {message}"
        ),
        file: Optional[Path] = None,
        file_rotation: str = "3 days",
        file_retention: str = "1 week",
        interceptions: Sequence[str] = [
            "uvicorn",
            "uvicorn.access",
            "uvicorn.error",
            "uvicorn.asgi",
            "fastapi",
        ],
    ) -> LoggerInstance:
        logger.remove()

        if mode in ["console", "all"]:
            logger.add(
                sys.stdout,
                enqueue=True,
                backtrace=True,
                level=level.upper(),
                format=console_format,
                filter=lambda record: record["level"].name
                in ["INFO", "WARNING", "DEBUG", "TRACE"],
            )
            logger.add(
                sys.stderr,
                enqueue=True,
                backtrace=True,
                level=level.upper(),
                format=console_format,
                filter=lambda record: record["level"].name in ["ERROR", "CRITICAL"],
            )

        if mode in ["file", "all"]:
            logger.add(
                str(file),
                rotation=file_rotation,
                retention=file_retention,
                enqueue=True,
                backtrace=True,
                level=level.upper(),
                format=file_format,
            )

        logging.basicConfig(
            handlers=[InterceptHandler()], level=logging.NOTSET, force=True
        )

        for external_logger in interceptions:
            logging.getLogger(external_logger).handlers = [InterceptHandler()]

        Logger.__instance__ = logger

        return logger  # type: ignore

    @staticmethod
    def instance() -> Optional[LoggerInstance]:
        return Logger.__instance__

    @staticmethod
    def uvicorn_config(level: LogLevel) -> dict:
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "default": {"class": "materia_server.core.logging.InterceptHandler"},
                "access": {"class": "materia_server.core.logging.InterceptHandler"},
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["default"],
                    "level": level.upper(),
                    "propagate": False,
                },
                "uvicorn.error": {"level": level.upper()},
                "uvicorn.access": {
                    "handlers": ["access"],
                    "level": level.upper(),
                    "propagate": False,
                },
            },
        }
