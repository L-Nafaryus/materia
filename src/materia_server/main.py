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

from materia_server import config as _config
from materia_server.config import Config
from materia_server._logging import make_logger, uvicorn_log_config, Logger
from materia_server.models import Database, DatabaseError, Cache
from materia_server import routers
from materia_server.app import make_application


@click.group()
def server():
    pass


@server.command()
@click.option("--config_path", type=Path)
@from_pydantic("application", _config.Application, prefix="app")
@from_pydantic("log", _config.Log, prefix="log")
def start(application: _config.Application, config_path: Path, log: _config.Log):
    config = Config()
    config.log = log
    logger = make_logger(config)

    # if user := application.user:
    #    os.setuid(pwd.getpwnam(user).pw_uid)
    # if group := application.group:
    #    os.setgid(pwd.getpwnam(user).pw_gid)
    # TODO: merge cli options with config
    if working_directory := (
        application.working_directory or config.application.working_directory
    ).resolve():
        try:
            os.chdir(working_directory)
        except FileNotFoundError as e:
            logger.error("Failed to change working directory: {}", e)
            sys.exit()
    logger.debug(f"Current working directory: {working_directory}")

    # check the configuration file or use default
    if config_path is not None:
        config_path = config_path.resolve()
        try:
            logger.debug("Reading configuration file at {}", config_path)
            if not config_path.exists():
                logger.error("Configuration file was not found at {}.", config_path)
                sys.exit(1)
            else:
                config = Config.open(config_path.resolve())
        except Exception as e:
            logger.error("Failed to read configuration file: {}", e)
            sys.exit(1)
    else:
        # trying to find configuration file in the current working directory
        config_path = Config.data_dir().joinpath("config.toml")
        if config_path.exists():
            logger.info("Found configuration file in the current working directory.")
            try:
                config = Config.open(config_path)
            except Exception as e:
                logger.error("Failed to read configuration file: {}", e)
            else:
                logger.info("Using the default configuration.")
                config = Config()
        else:
            logger.info("Using the default configuration.")
            config = Config()

    config.log.level = log.level
    logger = make_logger(config)
    if working_directory := config.application.working_directory.resolve():
        logger.debug(f"Change working directory: {working_directory}")
        try:
            os.chdir(working_directory)
        except FileNotFoundError as e:
            logger.error("Failed to change working directory: {}", e)
            sys.exit()

    config.application.mode = application.mode

    try:
        uvicorn.run(
            make_application(config, logger),
            port=config.server.port,
            host=str(config.server.address),
            # reload = config.application.mode == "development",
            log_config=uvicorn_log_config(config),
        )
    except (KeyboardInterrupt, SystemExit):
        pass


@server.group()
def config():
    pass


@config.command("create", help="Create a new configuration file.")
@click.option(
    "--path",
    "-p",
    type=Path,
    default=Path.cwd().joinpath("config.toml"),
    help="Path to the file.",
)
@click.option(
    "--force", "-f", is_flag=True, default=False, help="Overwrite a file if exists."
)
def config_create(path: Path, force: bool):
    path = path.resolve()
    config = Config()
    logger = make_logger(config)

    if path.exists() and not force:
        logger.warning("File already exists at the given path. Exit.")
        sys.exit(1)

    if not path.parent.exists():
        logger.info("Creating directory at {}", path)
        path.mkdir(parents=True)

    logger.info("Writing configuration file at {}", path)
    config.write(path)
    logger.info("All done.")


@config.command("check", help="Check the configuration file.")
@click.option(
    "--path",
    "-p",
    type=Path,
    default=Path.cwd().joinpath("config.toml"),
    help="Path to the file.",
)
def config_check(path: Path):
    path = path.resolve()
    config = Config()
    logger = make_logger(config)

    if not path.exists():
        logger.error("Configuration file was not found at the given path. Exit.")
        sys.exit(1)

    try:
        Config.open(path)
    except Exception as e:
        logger.error("{}", e)
    else:
        logger.info("OK.")


if __name__ == "__main__":
    server()
