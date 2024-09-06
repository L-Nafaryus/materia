from fastapi import APIRouter, Request, Response, status, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import mimetypes
from pathlib import Path
from materia.core.misc import optional
from materia.routers import middleware

from materia import docs as materia_docs

router = APIRouter()

# templates = Jinja2Templates(directory=Path(materia_docs.__path__[0]))
# p = Path(__file__).parent.joinpath("..", "docs").resolve()
# router.mount("/docs", StaticFiles(directory="doces", html=True), name="docs")


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
