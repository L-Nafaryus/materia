from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["root"])

try:
    import materia_frontend
except ModuleNotFoundError:
    pass
else:

    templates = Jinja2Templates(directory=Path(materia_frontend.__path__[0]) / "dist")

    @router.get("/{spa:path}", response_class=HTMLResponse)
    async def root(request: Request):
        return templates.TemplateResponse(
            "base.html", {"request": request, "view": "app"}
        )