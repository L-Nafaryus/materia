from typing import Optional, Sequence
import uuid
from datetime import datetime
from fastapi import HTTPException, Request, Response, status, Depends, Cookie
from fastapi.security.base import SecurityBase
import jwt
from sqlalchemy import select 
from pydantic import BaseModel
from enum import StrEnum
from http import HTTPMethod as HttpMethod
from fastapi.security import HTTPBearer,  OAuth2PasswordBearer, OAuth2PasswordRequestForm, APIKeyQuery, APIKeyCookie, APIKeyHeader

from materia_server import security
from materia_server.models import User


class Context:
    def __init__(self, request: Request):
        self.config = request.state.config
        self.database = request.state.database 
        self.cache = request.state.cache 
        self.logger = request.state.logger


async def jwt_cookie(request: Request, response: Response, ctx: Context = Depends()):
    if not (access_token := request.cookies.get(ctx.config.security.cookie_access_token_name)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing token")
    refresh_token = request.cookies.get(ctx.config.security.cookie_refresh_token_name)

    if ctx.config.oauth2.jwt_signing_algo in ["HS256", "HS384", "HS512"]:
        secret = ctx.config.oauth2.jwt_secret 
    else:
        secret = ctx.config.oauth2.jwt_signing_key

    issuer = "{}://{}".format(ctx.config.server.scheme, ctx.config.server.domain)

    try:
        refresh_claims = security.validate_token(refresh_token, secret) if refresh_token else None
        
        if refresh_claims:
            if refresh_claims.exp < datetime.now().timestamp():
                refresh_claims = None
    except jwt.PyJWTError:
        refresh_claims = None 

    try:
        access_claims = security.validate_token(access_token, secret)
        
        if access_claims.exp < datetime.now().timestamp():
            if refresh_claims:
                new_access_token = security.generate_token(
                    access_claims.sub, 
                    str(secret),
                    ctx.config.oauth2.access_token_lifetime,
                    issuer 
                )
                access_claims = security.validate_token(new_access_token, secret)
                response.set_cookie(
                    ctx.config.security.cookie_access_token_name, 
                    value = new_access_token, 
                    max_age = ctx.config.oauth2.access_token_lifetime, 
                    secure = True,
                    httponly = ctx.config.security.cookie_http_only,
                    samesite = "lax"
                )
            else:
                access_claims = None
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {e}")

    if not await User.by_id(uuid.UUID(access_claims.sub), ctx.database):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid user")

    return access_claims


async def user(claims = Depends(jwt_cookie), ctx: Context = Depends()):
    if not (current_user := await User.by_id(uuid.UUID(claims.sub), ctx.database)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing user")

    return current_user
