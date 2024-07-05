import shutil
from fastapi import APIRouter, Depends, HTTPException, status

from materia_server.models import User, Repository, RepositoryInfo
from materia_server.routers import middleware
from materia_server.config import Config


router = APIRouter(tags=["repository"])


@router.post("/repository")
async def create(
    user: User = Depends(middleware.user), ctx: middleware.Context = Depends()
):
    repository_path = Config.data_dir() / "repository" / user.lower_name

    if await Repository.by_user_id(user.id, ctx.database):
        raise HTTPException(status.HTTP_409_CONFLICT, "Repository already exists")

    repository = Repository(user_id=user.id, capacity=ctx.config.repository.capacity)

    try:
        repository_path.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to created a repository"
        )

    await repository.create(ctx.database)


@router.get("/repository", response_model=RepositoryInfo)
async def info(
    user: User = Depends(middleware.user), ctx: middleware.Context = Depends()
):
    async with ctx.database.session() as session:
        session.add(user)
        await session.refresh(user, attribute_names=["repository"])

    if not (repository := user.repository):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository not found")

    async with ctx.database.session() as session:
        session.add(repository)
        await session.refresh(repository, attribute_names=["files"])

    return RepositoryInfo(
        capacity=repository.capacity,
        used=sum([file.size for file in repository.files]),
    )


@router.delete("/repository")
async def remove(
    user: User = Depends(middleware.user), ctx: middleware.Context = Depends()
):
    repository_path = Config.data_dir() / "repository" / user.lower_name

    async with ctx.database.session() as session:
        session.add(user)
        await session.refresh(user, attribute_names=["repository"])

    try:
        if repository_path.exists():
            shutil.rmtree(str(repository_path))
    except OSError:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to remove repository"
        )

    await user.repository.remove(ctx.database)
