from pathlib import Path
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import mimetypes

router = APIRouter()

try:
    import materia_frontend
except ModuleNotFoundError:
    pass
else:

    templates = Jinja2Templates(
        directory=Path(materia_frontend.__path__[0], "templates")
    )

    @router.get("/assets/{filename}")
    async def assets(filename: str, include_in_schema=False):
        path = Path(materia_frontend.__path__[0]).joinpath("assets", filename)

        if not path.exists():
            return Response(status_code=status.HTTP_404_NOT_FOUND)

        content = path.read_bytes()
        mime = mimetypes.guess_type(path)[0]

        return Response(content, media_type=mime)

    @router.get("/{spa:path}", response_class=HTMLResponse, include_in_schema=False)
    async def root(request: Request):
        return templates.TemplateResponse(request, "base.html", {"view": "app"})
