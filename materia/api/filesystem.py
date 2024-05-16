import os
import time
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from sqlalchemy import and_, insert, select, update

from materia import db
from materia.api.depends import DatabaseState
from materia.api.middleware import JwtMiddleware
from materia.config import Config


router = APIRouter(tags = ["filesystem"])


@router.put("/file/upload", dependencies = [Depends(JwtMiddleware())])
async def upload(request: Request, file: UploadFile, database: DatabaseState = Depends(), directory_path: Path = Path()):
    print("hi")
    user = request.state.user
    repository_path = Config.data_dir() / "repository" / user.login_name.lower()
    blacklist = [os.sep, ".", "..", "*"]
    directory_path = Path(os.sep.join(filter(lambda part: part not in blacklist, directory_path.parts)))

    async with database.session() as session:
        session.add(user)
        await session.refresh(user, attribute_names = ["repository"])
        if not (repository := user.repository):
            repository = db.Repository(
                owner_id = user.id,
                capacity = 10 * 1024 * 1024 * 1024
            )
            session.add(repository)

            try:
                repository_path.mkdir(parents = True, exist_ok = True)
            except OSError:
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to created a repository")
            
            await session.commit()

    async with database.session() as session:
        current_directory = None
        current_path = Path()
        directory = None

        for part in directory_path.parts:
            if not (directory := (await session.scalars(select(db.Directory).where(and_(db.Directory.name == part, db.Directory.path == str(current_path)))))).first():
                directory = db.Directory(
                    repository_id = repository.id,
                    parent_id = current_directory.id if current_directory else None,
                    name = part,
                    path = str(current_path)
                )
                session.add(directory)

            current_directory = directory 
            current_path /= part

        try:
            (repository_path / directory_path).mkdir(parents = True, exist_ok = True)
        except OSError:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to created a directory")

        await session.commit()

    async with database.session() as session:
        if file_ := (await session.scalars(select(db.File).where(and_(db.File.name == file.filename, db.File.path == str(directory_path))))).first():
            print(file_.__dict__)
            await session.execute(update(db.File).where(db.File.id == file_.id).values(updated_unix = time.time(), size = file.size))
        else:
            file_ = db.File(
                repository_id = repository.id,
                parent_id = directory.id if directory else None,
                name = file.filename,
                path = str(directory_path),
                size = file.size
            )
            session.add(file_)

        try:
            (repository_path / directory_path / file.filename).write_bytes(await file.read())
        except OSError:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to write a file")

        await session.commit()

