import os
import time
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, insert, select, update

from materia import db
from materia.api import schema
from materia.api.state import ConfigState, DatabaseState
from materia.api.middleware import JwtMiddleware
from materia.config import Config


router = APIRouter(tags = ["repository"])

@router.post("/repository", dependencies = [Depends(JwtMiddleware())])
async def create(request: Request, config: ConfigState = Depends(), database: DatabaseState = Depends()):
    user = request.state.user
    repository_path = Config.data_dir() / "repository" / user.login_name.lower()

    async with database.session() as session:
        session.add(user)
        await session.refresh(user, attribute_names = ["repository"])

        if not (repository := user.repository):
            repository = db.Repository(
                owner_id = user.id,
                capacity = config.repository.capacity
            )
            session.add(repository)

            try:
                repository_path.mkdir(parents = True, exist_ok = True)
            except OSError:
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to created a repository")
            
            await session.commit()

        else:
            raise HTTPException(status.HTTP_409_CONFLICT, "Repository already exists")

@router.get("/repository", dependencies = [Depends(JwtMiddleware())])
async def info(request: Request, database: DatabaseState = Depends()):
    user = request.state.user 

    async with database.session() as session:
        session.add(user)
        await session.refresh(user, attribute_names = ["repository"])

        if repository := user.repository:
            await session.refresh(repository, attribute_names = ["files"])
            
            return schema.RepositoryInfo(
                capacity = repository.capacity,
                used = sum([ file.size for file in repository.files ])
            )

        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository is not found")
