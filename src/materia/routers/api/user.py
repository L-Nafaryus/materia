import uuid
import io
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from materia.models import User, UserInfo
from materia.routers import middleware


router = APIRouter(tags=["user"])


@router.get("/user", response_model=UserInfo)
async def info(
    claims=Depends(middleware.jwt_cookie), ctx: middleware.Context = Depends()
):
    async with ctx.database.session() as session:
        if not (current_user := await User.by_id(uuid.UUID(claims.sub), session)):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing user")

    return current_user.info()


@router.delete("/user")
async def remove(
    user: User = Depends(middleware.user), ctx: middleware.Context = Depends()
):
    try:
        async with ctx.database.session() as session:
            await user.remove(session)
            await session.commit()

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to remove user: {e}"
        ) from e


@router.put("/user/avatar")
async def avatar(
    file: UploadFile,
    user: User = Depends(middleware.user),
    ctx: middleware.Context = Depends(),
):
    async with ctx.database.session() as session:
        try:
            await user.edit_avatar(io.BytesIO(await file.read()), session, ctx.config)
            await session.commit()
        except Exception as e:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                f"{e}",
            )


@router.delete("/user/avatar")
async def remove_avatar(
    user: User = Depends(middleware.user),
    ctx: middleware.Context = Depends(),
):
    async with ctx.database.session() as session:
        try:
            await user.edit_avatar(None, session, ctx.config)
            await session.commit()
        except Exception as e:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                f"{e}",
            )
