from typing import Annotated, Optional
from pathlib import Path
from fastapi import (
    Request,
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File as _File,
    Form,
)
from fastapi.responses import JSONResponse
from materia.models import (
    User,
    File,
    FileInfo,
    Directory,
    Repository,
    FileRename,
    FileCopyMove,
)
from materia.core import (
    SessionContext,
    Config,
    FileSystem,
    TemporaryFileTarget,
    Database,
)
from materia.routers import middleware
from materia.routers.api.directory import validate_target_directory
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import ValueTarget
from starlette.requests import ClientDisconnect
from aiofiles import ospath as async_path
from materia.tasks import remove_cache_file

router = APIRouter(tags=["file"])


async def validate_current_file(
    path: Path, repository: Repository, session: SessionContext, config: Config
) -> Directory:
    if not FileSystem.check_path(path):
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Invalid path")

    if not (
        file := await File.by_path(
            repository,
            FileSystem.normalize(path),
            session,
            config,
        )
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found")

    return file


class FileSizeValidator:
    def __init__(self, capacity: int):
        self.body = 0
        self.capacity = capacity

    def __call__(self, chunk: bytes):
        self.body += len(chunk)
        if self.body > self.capacity:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)


@router.post("/file")
async def create(
    request: Request,
    repository: Repository = Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    async with ctx.database.session() as session:
        capacity = await repository.remaining_capacity(session)

    try:
        file = TemporaryFileTarget(
            ctx.config.application.working_directory,
            validator=FileSizeValidator(capacity),
        )
        path = ValueTarget()

        ctx.logger.debug(f"Shedule remove cache file: {file.path().name}")
        remove_cache_file.apply_async(args=(file.path(), ctx.config), countdown=10)

        parser = StreamingFormDataParser(headers=request.headers)
        parser.register("file", file)
        parser.register("path", path)

        async for chunk in request.stream():
            parser.data_received(chunk)

    except ClientDisconnect:
        file.remove()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Client disconnect")
    except HTTPException as e:
        file.remove()
        raise e
    except Exception as e:
        file.remove()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, " ".join(e.args))

    path = Path(path.value.decode())

    if not file.multipart_filename:
        file.remove()
        raise HTTPException(
            status.HTTP_417_EXPECTATION_FAILED, "Cannot upload file without name"
        )
    if not FileSystem.check_path(path):
        file.remove()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Invalid path")

    async with ctx.database.session() as session:
        target_directory = await validate_target_directory(
            path, repository, session, ctx.config
        )

        try:
            await File(
                repository_id=repository.id,
                parent_id=target_directory.id if target_directory else None,
                name=file.multipart_filename,
                size=await async_path.getsize(file.path()),
            ).new(file.path(), session, ctx.config)
        except Exception:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to create file"
            )
        else:
            await session.commit()


@router.get("/file", response_model=FileInfo)
async def info(
    path: Path,
    repository: Repository = Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    async with ctx.database.session() as session:
        file = await validate_current_file(path, repository, session, ctx.config)

        info = file.info()

        return info


@router.delete("/file")
async def remove(
    path: Path,
    repository: Repository = Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    async with ctx.database.session() as session:
        file = await validate_current_file(path, repository, session, ctx.config)

        await file.remove(session, ctx.config)
        await session.commit()


@router.patch("/file/rename")
async def rename(
    data: FileRename,
    repository: Repository = Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    async with ctx.database.session() as session:
        file = await validate_current_file(data.path, repository, session, ctx.config)

        await file.rename(data.name, session, ctx.config, force=data.force)
        await session.commit()


@router.patch("/file/move")
async def move(
    data: FileCopyMove,
    repository: Repository = Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    async with ctx.database.session() as session:
        file = await validate_current_file(data.path, repository, session, ctx.config)
        target_directory = await validate_target_directory(
            data.target, repository, session, ctx.config
        )

        await file.move(target_directory, session, ctx.config, force=data.force)
        await session.commit()


@router.post("/file/copy")
async def copy(
    data: FileCopyMove,
    repository: Repository = Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    async with ctx.database.session() as session:
        file = await validate_current_file(data.path, repository, session, ctx.config)
        target_directory = await validate_target_directory(
            data.target, repository, session, ctx.config
        )

        await file.copy(target_directory, session, ctx.config, force=data.force)
        await session.commit()
