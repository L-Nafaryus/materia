from fastapi import APIRouter, Depends, HTTPException, status, Response
from PIL import Image
import io
from pathlib import Path
import mimetypes

from materia.routers import middleware
from materia.core import Config

router = APIRouter(tags=["resources"], prefix="/resources")


@router.get("/avatars/{avatar_id}")
async def avatar(
    avatar_id: str, format: str = "png", ctx: middleware.Context = Depends()
):
    avatar_path = Config.data_dir() / "avatars" / avatar_id
    format = format.upper()

    if not avatar_path.exists():
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Failed to find the given avatar"
        )

    try:
        img = Image.open(avatar_path)
        buffer = io.BytesIO()

        if format == "JPEG":
            img.convert("RGB")

        img.save(buffer, format=format)

    except OSError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Failed to process image file"
        )

    return Response(content=buffer.getvalue(), media_type=Image.MIME[format])


try:
    import materia_frontend
except ModuleNotFoundError:
    pass
else:

    @router.get("/assets/{filename}")
    async def assets(filename: str):
        path = Path(materia_frontend.__path__[0]).joinpath(
            "dist", "resources", "assets", filename
        )

        if not path.exists():
            return Response(status_code=status.HTTP_404_NOT_FOUND)

        content = path.read_bytes()
        mime = mimetypes.guess_type(path)[0]

        return Response(content, media_type=mime)
