from pathlib import Path
import sys
import click
from materia.core.config import Config
from materia.core.logging import Logger
from materia.app import Application
import asyncio


@click.group()
def cli():
    pass


@cli.command()
@click.option("--config", type=Path)
def start(config: Path):
    config_path = config
    logger = Logger.new()

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

    async def main():
        app = await Application.new(config)
        await app.start()

    asyncio.run(main())


@cli.group()
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
    logger = Logger.new()

    if path.exists() and not force:
        logger.warning("File already exists at the given path. Exit.")
        sys.exit(1)

    if not path.parent.exists():
        logger.info("Creating directory at {}", path)
        path.parent.mkdir(parents=True)

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
    logger = Logger.new()

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
    cli()
