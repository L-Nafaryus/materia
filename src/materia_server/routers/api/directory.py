import os
from pathlib import Path
import shutil

from fastapi import APIRouter, Depends, HTTPException, status

from materia_server.models import User, Directory, DirectoryInfo
from materia_server.routers import middleware
from materia_server.config import Config


router = APIRouter(tags=["directory"])


@router.post("/directory")
async def create(
    path: Path = Path(),
    user: User = Depends(middleware.user),
    ctx: middleware.Context = Depends(),
):
    repository_path = Config.data_dir() / "repository" / user.lower_name
    blacklist = [os.sep, ".", "..", "*"]
    directory_path = Path(
        os.sep.join(filter(lambda part: part not in blacklist, path.parts))
    )

    async with ctx.database.session() as session:
        session.add(user)
        await session.refresh(user, attribute_names=["repository"])

    if not user.repository:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository not found")

    current_directory = None
    current_path = Path()
    directory = None

    for part in directory_path.parts:
        if not await Directory.by_path(
            user.repository.id, current_path, part, ctx.database
        ):
            directory = Directory(
                repository_id=user.repository.id,
                parent_id=current_directory.id if current_directory else None,
                name=part,
                path=None if current_path == Path() else str(current_path),
            )

            try:
                (repository_path / current_path / part).mkdir(exist_ok=True)
            except OSError:
                raise HTTPException(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    f"Failed to create a directory {current_path / part}",
                )

            async with ctx.database.session() as session:
                session.add(directory)
                await session.commit()
                await session.refresh(directory)

        current_directory = directory
        current_path /= part


@router.get("/directory")
async def info(
    path: Path,
    user: User = Depends(middleware.user),
    ctx: middleware.Context = Depends(),
):
    async with ctx.database.session() as session:
        session.add(user)
        await session.refresh(user, attribute_names=["repository"])

    if not user.repository:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository not found")

    if not (
        directory := await Directory.by_path(
            user.repository.id,
            None if path.parent == Path() else path.parent,
            path.name,
            ctx.database,
        )
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Directory not found")

    async with ctx.database.session() as session:
        session.add(directory)
        await session.refresh(directory, attribute_names=["files"])

    info = DirectoryInfo.model_validate(directory)
    info.used = sum([file.size for file in directory.files])

    return info


@router.delete("/directory")
async def remove(
    path: Path,
    user: User = Depends(middleware.user),
    ctx: middleware.Context = Depends(),
):
    repository_path = Config.data_dir() / "repository" / user.lower_name

    async with ctx.database.session() as session:
        session.add(user)
        await session.refresh(user, attribute_names=["repository"])

    if not user.repository:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository not found")

    if not (
        directory := await Directory.by_path(
            user.repository.id,
            None if path.parent == Path() else path.parent,
            path.name,
            ctx.database,
        )
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Directory not found")

    directory_path = repository_path / path

    try:
        if directory_path.is_dir():
            shutil.rmtree(str(directory_path))
    except OSError:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to remove directory"
        )

    await directory.remove(ctx.database)
