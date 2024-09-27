from fastapi import APIRouter, Request, Response, status, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import mimetypes
from pathlib import Path
from materia.core.misc import optional
from materia.routers import middleware


router = APIRouter()


try:
    from materia import docs as materia_docs
except ImportError:
    pass
else:

    @router.get("/docs/{catchall:path}", include_in_schema=False)
    async def docs(request: Request, ctx: middleware.Context = Depends()):
        docs_directory = Path(materia_docs.__path__[0]).resolve()
        target = docs_directory.joinpath(request.path_params["catchall"]).resolve()

        if not optional(target.relative_to, docs_directory):
            raise HTTPException(status.HTTP_403_FORBIDDEN)

        if target.is_dir() and (index := target.joinpath("index.html")).is_file():
            return FileResponse(index)

        if not target.is_file():
            raise HTTPException(status.HTTP_404_NOT_FOUND)

        return FileResponse(target)
