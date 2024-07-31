import uuid
import io
import shutil

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
import sqlalchemy as sa
from sqids.sqids import Sqids
from PIL import Image

from materia.config import Config
from materia.models import User, UserInfo
from materia.routers import middleware


router = APIRouter(tags=["user"])


@router.get("/user", response_model=UserInfo)
async def info(
    claims=Depends(middleware.jwt_cookie), ctx: middleware.Context = Depends()
):
    if not (current_user := await User.by_id(uuid.UUID(claims.sub), ctx.database)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing user")

    info = UserInfo.model_validate(current_user)
    if current_user.is_email_private:
        info.email = None

    return info


@router.delete("/user")
async def remove(
    user: User = Depends(middleware.user), ctx: middleware.Context = Depends()
):
    repository_path = Config.data_dir() / "repository" / user.lower_name

    async with ctx.database.session() as session:
        session.add(user)
        await session.refresh(user, attribute_names=["repository"])

    try:
        if repository_path.exists():
            shutil.rmtree(str(repository_path))
    except OSError:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to remove user"
        )

    await user.repository.remove(ctx.database)


@router.post("/user/avatar")
async def avatar(
    file: UploadFile,
    user: User = Depends(middleware.user),
    ctx: middleware.Context = Depends(),
):
    async with ctx.database.session() as session:
        avatars: list[str] = (await session.scalars(sa.select(User.avatar))).all()
        avatars = list(filter(lambda avatar_hash: avatar_hash, avatars))

    avatar_id = Sqids(min_length=10, blocklist=avatars).encode([len(avatars)])

    try:
        img = Image.open(io.BytesIO(await file.read()))
    except OSError as _:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Failed to read file data"
        )

    try:
        if not (avatars_dir := Config.data_dir() / "avatars").exists():
            avatars_dir.mkdir()
        img.save(avatars_dir / avatar_id, format=img.format)
    except OSError as _:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to save avatar"
        )

    if old_avatar := user.avatar:
        if (old_file := Config.data_dir() / "avatars" / old_avatar).exists():
            old_file.unlink()

    async with ctx.database.session() as session:
        await session.execute(
            sa.update(User).where(User.id == user.id).values(avatar=avatar_id)
        )
        await session.commit()
