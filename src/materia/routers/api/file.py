import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile

from materia.models import (
    User,
    File,
    FileInfo,
    Directory,
    DirectoryPath,
    Repository,
    FileSystem,
    FileRename,
    FilePath,
    FileCopyMove,
)
from materia.models.database import SessionContext
from materia.routers import middleware
from materia.config import Config
from materia.routers.api.directory import validate_target_directory

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


@router.post("/file")
async def create(
    file: UploadFile,
    path: DirectoryPath,
    repository: Repository = Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    if not file.filename:
        raise HTTPException(
            status.HTTP_417_EXPECTATION_FAILED, "Cannot upload file without name"
        )
    if not FileSystem.check_path(path.path):
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Invalid path")

    async with ctx.database.session() as session:
        target_directory = await validate_target_directory(
            path.path, repository, session, ctx.config
        )

        await File(
            repository_id=repository.id,
            parent_id=target_directory.id if target_directory else None,
            name=file.filename,
            size=file.size,
        ).new(await file.read(), session, ctx.config)

        await session.commit()


@router.get("/file")
async def info(
    path: Path,
    repository: Repository = Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    async with ctx.database.session() as session:
        file = await validate_current_file(path, repository, session, ctx.config)

        info = await file.info(session)

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
