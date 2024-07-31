from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from os import environ
import os
from pathlib import Path
import pwd
import sys
from typing import AsyncIterator, TypedDict
import click

from pydantic import BaseModel
from pydanclick import from_pydantic
import pydantic
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from materia import config as _config
from materia.config import Config
from materia._logging import make_logger, uvicorn_log_config, Logger
from materia.models import (
    Database,
    DatabaseError,
    DatabaseMigrationError,
    Cache,
    CacheError,
)
from materia import routers


class AppContext(TypedDict):
    config: Config
    logger: Logger
    database: Database
    cache: Cache


def make_lifespan(config: Config, logger: Logger):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[AppContext]:

        try:
            logger.info("Connecting to database {}", config.database.url())
            database = await Database.new(config.database.url())  # type: ignore

            logger.info("Running migrations")
            await database.run_migrations()

            logger.info("Connecting to cache {}", config.cache.url())
            cache = await Cache.new(config.cache.url())  # type: ignore
        except DatabaseError as e:
            logger.error(f"Failed to connect postgres: {e}")
            sys.exit()
        except DatabaseMigrationError as e:
            logger.error(f"Failed to run migrations: {e}")
            sys.exit()
        except CacheError as e:
            logger.error(f"Failed to connect redis: {e}")
            sys.exit()

        yield AppContext(config=config, database=database, cache=cache, logger=logger)

        if database.engine is not None:
            await database.dispose()

    return lifespan


def make_application(config: Config, logger: Logger):
    try:
        import materia_frontend
    except ModuleNotFoundError:
        logger.warning(
            "`materia_frontend` is not installed. No user interface will be served."
        )

    app = FastAPI(
        title="materia",
        version="0.1.0",
        docs_url="/api/docs",
        lifespan=make_lifespan(config, logger),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(routers.api.router)
    app.include_router(routers.resources.router)
    app.include_router(routers.root.router)

    return app
