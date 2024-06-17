import os
import time
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, insert, select, update

from materia import db
from materia.api.state import ConfigState, DatabaseState
from materia.api.middleware import JwtMiddleware
from materia.config import Config
from materia.api import schema


router = APIRouter(tags = ["directory"])

@router.post("/directory", dependencies = [Depends(JwtMiddleware())])
async def create(request: Request, path: Path = Path(), config: ConfigState = Depends(), database: DatabaseState = Depends()):
    user = request.state.user
    repository_path = Config.data_dir() / "repository" / user.login_name.lower()
    blacklist = [os.sep, ".", "..", "*"]
    directory_path = Path(os.sep.join(filter(lambda part: part not in blacklist, path.parts)))

    async with database.session() as session:
        session.add(user)
        await session.refresh(user, attribute_names = ["repository"])

        current_directory = None
        current_path = Path()
        directory = None

        for part in directory_path.parts:
            if not (directory := (await session
                .scalars(select(db.Directory)
                .where(and_(db.Directory.name == part, db.Directory.path == str(current_path))))
            ).first()):
                directory = db.Directory(
                    repository_id = user.repository.id,
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

@router.get("/directory", dependencies = [Depends(JwtMiddleware())])
async def info(request: Request, repository_id: int, path: Path, config: ConfigState = Depends(), database: DatabaseState = Depends()):
    async with database.session() as session:
        if directory := (await session
            .scalars(select(db.Directory)
            .where(and_(db.Directory.repository_id == repository_id, db.Directory.name == path.name, db.Directory.path == path.parent))
        )).first():
            await session.refresh(directory, attribute_names = ["files"])
            return schema.DirectoryInfo(
                id = directory.id,
                created_at = directory.created_unix,
                updated_at = directory.updated_unix,
                name = directory.name,
                path = directory.path,
                is_public = directory.is_public,
                used = sum([ file.size for file in directory.files ])
            )

        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository is not found")
