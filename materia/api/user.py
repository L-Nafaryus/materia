import io
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile, status
from sqlalchemy import delete, select, insert, func, or_, update
import bcrypt
from sqids import Sqids
from PIL import Image


from materia.config import Config
from materia.api.middleware import JwtMiddleware
from materia import db
from materia.api import schema
from materia.api.depends import ConfigState, DatabaseState 
from materia.api.token import TokenClaims


router = APIRouter(tags = ["user"])


@router.post("/user/register", response_model = schema.User)
async def register(body: schema.NewUser, database: DatabaseState = Depends()):

    async with database.session() as session:
        count: Optional[int] = await session.scalar(select(func.count(db.User.id)))

        user = (await session.scalars(
            select(db.User)
                .where(or_(db.User.login_name == body.login, db.User.email == body.email)
        ))).first()

    if user is not None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "User already exists")

    hashed_password = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()

    new_user = db.User(
        login_name = body.login,
        hashed_password = hashed_password,
        name = body.login,
        email = body.email,
        is_admin = count == 0,
    )
    
    async with database.session() as session:
        user = (await session.scalars(insert(db.User).returning(db.User), [new_user.__dict__])).first()
        await session.commit()

    return schema.User.from_(user)

@router.post("/user/remove", status_code = 200)
async def remove(body: schema.RemoveUser, database: DatabaseState = Depends()):
    async with database.session() as session:
        await session.execute(delete(db.User).where(db.User.id == body.id))
        await session.commit()

@router.post("/user/login", status_code = 200, response_model = schema.Token)
async def login(body: schema.LoginUser, response: Response, database: DatabaseState = Depends(), config: ConfigState = Depends()) -> Any:
    query = select(db.User)
    if login := body.login:
        query = query.where(db.User.login_name == login)
    elif email := body.email:
        query = query.where(db.User.email == email)
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing credentials")

    async with database.session() as session:
        if not (user := (await session.scalars(query)).first()):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    if not bcrypt.checkpw(body.password.encode(), user.hashed_password.encode()):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid password")

    token = TokenClaims.create(
        str(user.id),
        config.jwt.secret,
        config.jwt.maxage
    )

    response.set_cookie(
        "token", 
        value = token, 
        max_age = config.jwt.maxage, 
        secure = True, 
        httponly = True, 
        samesite = "none"
    )

    return schema.Token(access_token = token)

@router.get("/user/logout", status_code = 200)
async def logout(response: Response):
    response.set_cookie(
        "token", 
        value = "", 
        max_age = -1, 
        secure = True, 
        httponly = True, 
        samesite = "none"
    )

@router.get("/user/current", dependencies = [Depends(JwtMiddleware())], response_model = schema.User)
async def current(request: Request):
    return schema.User.from_(request.state.user)

@router.post("/user/avatar", dependencies = [Depends(JwtMiddleware())])
async def avatar(request: Request, file: UploadFile, database: DatabaseState = Depends()):
    async with database.session() as session:
        avatars: list[str] = (await session.scalars(select(db.User.avatar))).all()
        avatars = list(filter(lambda avatar_hash: avatar_hash, avatars))

    avatar_id = Sqids(min_length = 10, blocklist = avatars).encode([len(avatars)])

    try:
        img = Image.open(io.BytesIO(await file.read())) 
    except OSError as _:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Failed to read file data")

    try:
        if not (avatars_dir := Config.data_dir() / "avatars").exists():
            avatars_dir.mkdir()
        img.save(avatars_dir / avatar_id, format = img.format)
    except OSError as _:
        raise HTTPException(status.WS_1011_INTERNAL_ERROR, "Failed to save avatar")

    if old_avatar := request.state.user.avatar:
        if (old_file := Config.data_dir() / "avatars" / old_avatar).exists():
            old_file.unlink()

    async with database.session() as session:
        await session.execute(update(db.User).where(db.User.id == request.state.user.id).values(avatar = avatar_id))
        await session.commit()


