from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from materia.models import (
    User,
    Directory,
    DirectoryInfo,
    DirectoryPath,
    DirectoryRename,
    DirectoryCopyMove,
    Repository,
)
from materia.core import SessionContext, Config, FileSystem
from materia.routers import middleware

router = APIRouter(tags=["directory"])


async def validate_current_directory(
    path: Path, repository: Repository, session: SessionContext, config: Config
) -> Directory:
    if not FileSystem.check_path(path):
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Invalid path")

    if not (
        directory := await Directory.by_path(
            repository,
            FileSystem.normalize(path),
            session,
            config,
        )
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Directory not found")

    return directory


async def validate_target_directory(
    path: Path, repository: Repository, session: SessionContext, config: Config
) -> Directory:
    if not FileSystem.check_path(path):
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Invalid target path"
        )

    if FileSystem.normalize(path) == Path():
        # mean repository root
        target_directory = None
    else:
        if not (
            target_directory := await Directory.by_path(
                repository,
                FileSystem.normalize(path),
                session,
                config,
            )
        ):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Target directory not found")

    return target_directory


@router.post("/directory")
async def create(
    path: DirectoryPath,
    repository: Repository = Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    if not FileSystem.check_path(path.path):
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Invalid path")

    async with ctx.database.session() as session:
        current_directory = None
        current_path = Path()
        directory = None

        for part in FileSystem.normalize(path.path).parts:
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
    repository: Repository = Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    async with ctx.database.session() as session:
        directory = await validate_current_directory(
            path, repository, session, ctx.config
        )

        info = await directory.info(session)

        return info


@router.delete("/directory")
async def remove(
    path: Path,
    repository: Repository = Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    async with ctx.database.session() as session:
        directory = await validate_current_directory(
            path, repository, session, ctx.config
        )

        await directory.remove(session, ctx.config)
        await session.commit()


@router.patch("/directory/rename")
async def rename(
    data: DirectoryRename,
    repository: Repository = Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    async with ctx.database.session() as session:
        directory = await validate_current_directory(
            data.path, repository, session, ctx.config
        )

        await directory.rename(data.name, session, ctx.config, force=data.force)
        await session.commit()


@router.patch("/directory/move")
async def move(
    data: DirectoryCopyMove,
    repository: Repository = Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    async with ctx.database.session() as session:
        directory = await validate_current_directory(
            data.path, repository, session, ctx.config
        )
        target_directory = await validate_target_directory(
            data.target, repository, session, ctx.config
        )

        await directory.move(target_directory, session, ctx.config, force=data.force)
        await session.commit()


@router.post("/directory/copy")
async def copy(
    data: DirectoryCopyMove,
    repository: Repository = Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    async with ctx.database.session() as session:
        directory = await validate_current_directory(
            data.path, repository, session, ctx.config
        )
        target_directory = await validate_target_directory(
            data.target, repository, session, ctx.config
        )

        await directory.copy(target_directory, session, ctx.config, force=data.force)
        await session.commit()
