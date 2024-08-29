from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
import os
import sys
from typing import AsyncIterator, TypedDict, Self, Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from materia.core import (
    Config,
    Logger,
    LoggerInstance,
    Database,
    Cache,
    Cron,
)
from materia import routers


class Context(TypedDict):
    config: Config
    logger: LoggerInstance
    database: Database
    cache: Cache


class ApplicationError(Exception):
    pass


class Application:
    __instance__: Optional[Self] = None

    def __init__(
        self,
        config: Config,
        logger: LoggerInstance,
        database: Database,
        cache: Cache,
        cron: Cron,
        backend: FastAPI,
    ):
        if Application.__instance__:
            raise ApplicationError("Cannot create multiple applications")

        self.config = config
        self.logger = logger
        self.database = database
        self.cache = cache
        self.cron = cron
        self.backend = backend

    @staticmethod
    async def new(config: Config):
        if Application.__instance__:
            raise ApplicationError("Cannot create multiple applications")

        logger = Logger.new(**config.log.model_dump())

        # if user := config.application.user:
        #    os.setuid(pwd.getpwnam(user).pw_uid)
        # if group := config.application.group:
        #    os.setgid(pwd.getpwnam(user).pw_gid)
        logger.debug("Initializing application...")

        try:
            logger.debug("Changing working directory")
            os.chdir(config.application.working_directory.resolve())
        except FileNotFoundError as e:
            logger.error("Failed to change working directory: {}", e)
            sys.exit()

        try:
            logger.info("Connecting to database {}", config.database.url())
            database = await Database.new(config.database.url())  # type: ignore

            logger.info("Connecting to cache server {}", config.cache.url())
            cache = await Cache.new(config.cache.url())  # type: ignore

            logger.info("Prepairing cron")
            cron = Cron.new(
                config.cron.workers_count,
                backend_url=config.cache.url(),
                broker_url=config.cache.url(),
            )

            logger.info("Running database migrations")
            await database.run_migrations()
        except Exception as e:
            logger.error(" ".join(e.args))
            sys.exit()

        try:
            import materia_frontend
        except ModuleNotFoundError:
            logger.warning(
                "`materia_frontend` is not installed. No user interface will be served."
            )

        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncIterator[Context]:
            yield Context(config=config, logger=logger, database=database, cache=cache)

            if database.engine is not None:
                await database.dispose()

        backend = FastAPI(
            title="materia",
            version="0.1.0",
            docs_url="/api/docs",
            lifespan=lifespan,
        )
        backend.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost", "http://localhost:5173"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        backend.include_router(routers.api.router)
        backend.include_router(routers.resources.router)
        backend.include_router(routers.root.router)

        return Application(
            config=config,
            logger=logger,
            database=database,
            cache=cache,
            cron=cron,
            backend=backend,
        )

    @staticmethod
    def instance() -> Optional[Self]:
        return Application.__instance__

    async def start(self):
        self.logger.info(f"Spinning up cron workers [{self.config.cron.workers_count}]")
        self.cron.run_workers()

        try:
            # uvicorn.run(
            #    self.backend,
            #    port=self.config.server.port,
            #    host=str(self.config.server.address),
            #    # reload = config.application.mode == "development",
            #    log_config=Logger.uvicorn_config(self.config.log.level),
            # )
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
