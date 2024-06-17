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
from materia.api import repository, directory

router = APIRouter(tags = ["file"])

@router.put("/file", dependencies = [Depends(JwtMiddleware())])
async def upload(request: Request, file: UploadFile, directory_path: Path = Path(), config: ConfigState = Depends(), database: DatabaseState = Depends()):
    user = request.state.user 

    try:
        await repository.create(request, config = config, database = database) 
    except:
        pass

    #try:
    #    directory_info = directory.info
    #    await directory.create(request, path = directory_path, config = config, database = database)

    async with database.session() as session:
        if file_ := (await session
            .scalars(select(db.File)
            .where(and_(db.File.name == file.filename, db.File.path == str(directory_path))))
        ).first():
            await session.execute(update(db.File).where(db.File.id == file_.id).values(updated_unix = time.time(), size = file.size))
        else:
            file_ = db.File(
                repository_id = user.repository.id,
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
