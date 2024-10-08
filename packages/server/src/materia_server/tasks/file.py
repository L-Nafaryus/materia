from materia_server.core import Cron, CronError, SessionContext, Config, Database
from celery import shared_task
from fastapi import UploadFile
from materia_server.models import File
import asyncio
from pathlib import Path
from materia_server.core import FileSystem, Config


@shared_task(name="remove_cache_file")
def remove_cache_file(path: Path, config: Config):
    target = FileSystem(path, config.application.working_directory.joinpath("cache"))

    async def wrapper():
        await target.remove()

    asyncio.run(wrapper())
