import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile

from materia_server.models import User, File, FileInfo, Directory
from materia_server.routers import middleware
from materia_server.config import Config


router = APIRouter(tags = ["file"])

@router.post("/file")
async def create(upload_file: UploadFile, path: Path = Path(), user: User = Depends(middleware.user), ctx: middleware.Context = Depends()):
    if not upload_file.filename:
        raise HTTPException(status.HTTP_417_EXPECTATION_FAILED, "Cannot upload file without name")

    repository_path = Config.data_dir() / "repository" / user.lower_name
    blacklist = [os.sep, ".", "..", "*"]
    directory_path = Path(os.sep.join(filter(lambda part: part not in blacklist, path.parts)))

    async with ctx.database.session() as session:
        session.add(user)
        await session.refresh(user, attribute_names = ["repository"])

    if not user.repository:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository is not found")

    if not directory_path == Path():
        directory = await Directory.by_path(
            user.repository.id, 
            None if directory_path.parent == Path() else directory_path.parent, 
            directory_path.name, 
            ctx.database
        )

        if not directory:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Directory is not found")
    else:
        directory = None

    file = File(
        repository_id = user.repository.id,
        parent_id = directory.id if directory else None,
        name = upload_file.filename,
        path = None if directory_path == Path() else str(directory_path), 
        size = upload_file.size
    )

    try:
        file_path = repository_path.joinpath(directory_path, upload_file.filename)

        if file_path.exists():
            raise HTTPException(status.HTTP_409_CONFLICT, "File with given name already exists")

        file_path.write_bytes(await upload_file.read())
    except OSError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to write a file")

    async with ctx.database.session() as session:
        session.add(file)
        await session.commit()

@router.get("/file")
async def info(path: Path, user: User = Depends(middleware.user), ctx: middleware.Context = Depends()):
    async with ctx.database.session() as session:
        session.add(user)
        await session.refresh(user, attribute_names = ["repository"])

    if not user.repository:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository is not found")

    if not(file := await File.by_path(user.repository.id, None if path.parent == Path() else path.parent, path.name, ctx.database)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File is not found")

    info = FileInfo.model_validate(file)

    return info
