import os
from pathlib import Path
import shutil

from fastapi import APIRouter, Depends, HTTPException, status

from materia.models import User, Directory, DirectoryPath, DirectoryInfo, FileSystem
from materia.routers import middleware
from materia.config import Config

from pydantic import BaseModel

router = APIRouter(tags=["directory"])


@router.post("/directory")
async def create(
    path: DirectoryPath,
    repository=Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    if not FileSystem.check_path(path.path):
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Invalid path")

    path = FileSystem.normalize(path.path)

    async with ctx.database.session() as session:
        current_directory = None
        current_path = Path()
        directory = None

        for part in path.parts:
            if not (
                directory := await Directory.by_path(
                    repository, current_path.joinpath(part), session, ctx.config
                )
            ):
                directory = await Directory(
                    repository_id=repository.id,
                    parent_id=current_directory.id if current_directory else None,
                    name=part,
                ).new(session, ctx.config)

            current_directory = directory
            current_path /= part

        await session.commit()


@router.get("/directory")
async def info(
    path: Path,
    repository=Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    if not FileSystem.check_path(path):
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Invalid path")

    path = FileSystem.normalize(path)
    ctx.logger.info(path)
    async with ctx.database.session() as session:
        if not (
            directory := await Directory.by_path(
                repository,
                path,
                session,
                ctx.config,
            )
        ):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Directory not found")
        ctx.logger.info(directory)
        info = await directory.info(session)
        ctx.logger.info(info)
        return info


@router.delete("/directory")
async def remove(
    path: Path,
    repository=Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    if not FileSystem.check_path(path):
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Invalid path")

    path = FileSystem.normalize(path)

    async with ctx.database.session() as session:
        if not (
            directory := await Directory.by_path(
                repository,
                path,
                session,
                ctx.config,
            )
        ):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Directory not found")

        await directory.remove(session, ctx.config)


@router.patch("/directory/rename")
async def rename():
    pass


@router.patch("/directory/move")
async def move():
    pass


@router.post("/directory/copy")
async def copy():
    pass
