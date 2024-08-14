import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status

from materia.models import (
    User,
    Repository,
    RepositoryInfo,
    RepositoryContent,
    FileInfo,
    DirectoryInfo,
)
from materia.routers import middleware
from materia.config import Config


router = APIRouter(tags=["repository"])


@router.post("/repository")
async def create(
    user: User = Depends(middleware.user), ctx: middleware.Context = Depends()
):
    async with ctx.database.session() as session:
        if await Repository.from_user(user, session):
            raise HTTPException(status.HTTP_409_CONFLICT, "Repository already exists")

    async with ctx.database.session() as session:
        try:
            await Repository(
                user_id=user.id, capacity=ctx.config.repository.capacity
            ).new(session, ctx.config)
            await session.commit()
        except Exception as e:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, detail=" ".join(e.args)
            )


@router.get("/repository", response_model=RepositoryInfo)
async def info(
    repository=Depends(middleware.repository), ctx: middleware.Context = Depends()
):
    async with ctx.database.session() as session:
        return await repository.info(session)


@router.delete("/repository")
async def remove(
    repository=Depends(middleware.repository),
    ctx: middleware.Context = Depends(),
):
    try:
        async with ctx.database.session() as session:
            await repository.remove(session, ctx.config)
            await session.commit()
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"{e}")


@router.get("/repository/content", response_model=RepositoryContent)
async def content(
    repository=Depends(middleware.repository), ctx: middleware.Context = Depends()
):
    async with ctx.database.session() as session:
        session.add(repository)
        await session.refresh(repository, attribute_names=["directories"])
        await session.refresh(repository, attribute_names=["files"])

    content = RepositoryContent(
        files=list(
            map(
                lambda file: FileInfo.model_validate(file),
                filter(lambda file: file.path is None, repository.files),
            )
        ),
        directories=list(
            map(
                lambda directory: DirectoryInfo.model_validate(directory),
                filter(
                    lambda directory: directory.path is None, repository.directories
                ),
            )
        ),
    )

    return content
