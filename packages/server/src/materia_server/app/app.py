from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
import os
import sys
from typing import AsyncIterator, TypedDict, Self, Optional
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from materia_server.core import (
    Config,
    Logger,
    LoggerInstance,
    Database,
    Cache,
    Cron,
)
from materia_server import routers
from materia_server.core.misc import optional, optional_string


class Context(TypedDict):
    config: Config
    logger: LoggerInstance
    database: Database
    cache: Cache


class ApplicationError(Exception):
    pass


class Application:
    def __init__(
        self,
        config: Config,
    ):
        self.config: Config = config
        self.logger: Optional[LoggerInstance] = None
        self.database: Optional[Database] = None
        self.cache: Optional[Cache] = None
        self.cron: Optional[Cron] = None
        self.backend: Optional[FastAPI] = None

        self.prepare_logger()

    @staticmethod
    async def new(config: Config):
        app = Application(config)

        # if user := config.application.user:
        #    os.setuid(pwd.getpwnam(user).pw_uid)
        # if group := config.application.group:
        #    os.setgid(pwd.getpwnam(user).pw_gid)
        app.logger.debug("Initializing application...")
        await app.prepare_working_directory()

        try:
            await app.prepare_database()
            await app.prepare_cache()
            await app.prepare_cron()
            app.prepare_server()
        except Exception as e:
            app.logger.error(" ".join(e.args))
            sys.exit()

        return app

    def prepare_logger(self):
        self.logger = Logger.new(**self.config.log.model_dump())

    async def prepare_working_directory(self):
        try:
            path = self.config.application.working_directory.resolve()
            self.logger.debug(f"Changing working directory to {path}")
            os.chdir(path)
        except FileNotFoundError as e:
            self.logger.error("Failed to change working directory: {}", e)
            sys.exit()

    async def prepare_database(self):
        url = self.config.database.url()
        self.logger.info("Connecting to database {}", url)
        self.database = await Database.new(url)  # type: ignore

    async def prepare_cache(self):
        url = self.config.cache.url()
        self.logger.info("Connecting to cache server {}", url)
        self.cache = await Cache.new(url)  # type: ignore

    async def prepare_cron(self):
        url = self.config.cache.url()
        self.logger.info("Prepairing cron")
        self.cron = Cron.new(
            self.config.cron.workers_count, backend_url=url, broker_url=url
        )

    def prepare_server(self):
        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncIterator[Context]:
            yield Context(
                config=self.config,
                logger=self.logger,
                database=self.database,
                cache=self.cache,
            )

            if self.database.engine is not None:
                await self.database.dispose()

        self.backend = FastAPI(
            title="materia",
            version="0.1.0",
            docs_url=None,
            redoc_url=None,
            swagger_ui_init_oauth=None,
            swagger_ui_oauth2_redirect_url=None,
            openapi_url="/api/openapi.json",
            lifespan=lifespan,
        )
        self.backend.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost", "http://localhost:5173"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.backend.include_router(routers.api.router)
        if self.config.misc.enable_api_docs:
            self.backend.include_router(routers.api_docs.router)
        if self.config.misc.enable_docs:
            try:
                import materia_docs
            except ModuleNotFoundError:
                self.logger.error(
                    "The `misc.enable_docs` option was enabled but the `materia_docs` package was not found."
                )
            self.backend.include_router(routers.docs.router)
        if self.config.misc.enable_client:
            try:
                import materia_frontend
            except ModuleNotFoundError:
                self.logger.error(
                    "The `misc.enable_client` option was enabled but the `materia_frontend` package was not found."
                )
            self.backend.include_router(routers.client.router)

        for route in self.backend.routes:
            if isinstance(route, APIRoute):
                route.operation_id = (
                    optional_string(optional(route.tags.__getitem__, 0), "{}_")
                    + route.name
                )

    async def start(self):
        self.logger.info(f"Spinning up cron workers [{self.config.cron.workers_count}]")
        self.cron.run_workers()

        try:
            self.logger.info("Running database migrations")
            await self.database.run_migrations()

            uvicorn_config = uvicorn.Config(
                self.backend,
                port=self.config.server.port,
                host=str(self.config.server.address),
                log_config=Logger.uvicorn_config(self.config.log.level),
            )
            server = uvicorn.Server(uvicorn_config)

            await server.serve()
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("Exiting...")
            sys.exit()
        except Exception as e:
            self.logger.exception(" ".join(e.args), backtrace=False)
            sys.exit()
