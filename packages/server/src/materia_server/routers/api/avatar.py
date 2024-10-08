from fastapi import APIRouter, Depends, HTTPException, status, Response
from PIL import Image
import io

from materia_server.routers import middleware
from materia_server.core import Config

router = APIRouter(tags=["avatar"], prefix="/avatar")


@router.get("/{avatar_id}")
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
