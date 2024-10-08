from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status

from materia import security
from materia.routers.middleware import Context
from materia.models import LoginType, User, UserCredentials

router = APIRouter(tags=["auth"])


@router.post("/auth/signup")
async def signup(body: UserCredentials, ctx: Context = Depends()):
    if not User.check_username(body.name):
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid username"
        )
    if not User.check_password(body.password, ctx.config):
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password is too short (minimum length {ctx.config.security.password_min_length})",
        )

    async with ctx.database.session() as session:
        if await User.by_name(body.name, session, with_lower=True):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="User already exists")
        if await User.by_email(body.email, session):  # type: ignore
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already used")

        count: Optional[int] = await User.count(session)

        await User(
            name=body.name,
            lower_name=body.name.lower(),
            full_name=body.name,
            email=body.email,
            hashed_password=security.hash_password(
                body.password, algo=ctx.config.security.password_hash_algo
            ),
            login_type=LoginType.Plain,
            # first registered user is admin
            is_admin=count == 0,
        ).new(session, ctx.config)

        await session.commit()


@router.post("/auth/signin")
async def signin(body: UserCredentials, response: Response, ctx: Context = Depends()):
    async with ctx.database.session() as session:
        if (current_user := await User.by_name(body.name, session)) is None:
            if (current_user := await User.by_email(str(body.email), session)) is None:
                raise HTTPException(
                    status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
                )

    if not security.validate_password(
        body.password,
        current_user.hashed_password,
        algo=ctx.config.security.password_hash_algo,
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    issuer = "{}://{}".format(ctx.config.server.scheme, ctx.config.server.domain)
    secret = (
        ctx.config.oauth2.jwt_secret
        if ctx.config.oauth2.jwt_signing_algo in ["HS256", "HS384", "HS512"]
        else ctx.config.oauth2.jwt_signing_key
    )
    access_token = security.generate_token(
        str(current_user.id),
        str(secret),
        ctx.config.oauth2.access_token_lifetime,
        issuer,
    )
    refresh_token = security.generate_token(
        "", str(secret), ctx.config.oauth2.refresh_token_lifetime, issuer
    )

    response.set_cookie(
        ctx.config.security.cookie_access_token_name,
        value=access_token,
        max_age=ctx.config.oauth2.access_token_lifetime,
        secure=True,
        httponly=ctx.config.security.cookie_http_only,
        samesite="lax",
    )
    response.set_cookie(
        ctx.config.security.cookie_refresh_token_name,
        value=refresh_token,
        max_age=ctx.config.oauth2.refresh_token_lifetime,
        secure=True,
        httponly=ctx.config.security.cookie_http_only,
        samesite="lax",
    )


@router.get("/auth/signout")
async def signout(response: Response, ctx: Context = Depends()):
    response.delete_cookie(ctx.config.security.cookie_access_token_name)
    response.delete_cookie(ctx.config.security.cookie_refresh_token_name)
