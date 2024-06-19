from typing import Optional, Sequence
import uuid
from fastapi import HTTPException, Request, Response, status, Depends, Cookie
from fastapi.security.base import SecurityBase
import jwt
from sqlalchemy import select 
from pydantic import BaseModel
from enum import StrEnum
from http import HTTPMethod as HttpMethod
from fastapi.security import HTTPBearer,  OAuth2PasswordBearer, OAuth2PasswordRequestForm, APIKeyQuery, APIKeyCookie, APIKeyHeader

from materia_server import security
from materia_server.routers import context
from materia_server.models import user


async def get_token_claims(token, ctx: context.Context = Depends()) -> security.TokenClaims:
    try:
        secret = ctx.config.oauth2.jwt_secret if ctx.config.oauth2.jwt_signing_algo in ["HS256", "HS384", "HS512"] else ctx.config.oauth2.jwt_signing_key
        claims = security.validate_token(token, secret)
        user_id = uuid.UUID(claims.sub) # type: ignore
    except jwt.PyJWKError as _:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    except ValueError as _:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid token")

    if not (current_user := await user.User.by_id(user_id, ctx.database)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing user")

    return claims

class JwtBearer(HTTPBearer):
    def __init__(self, **kwargs):
        super().__init__(scheme_name = "Bearer", **kwargs)
        self.claims = None 

    async def __call__(self, request: Request, ctx: context.Context = Depends()):
        if credentials := await super().__call__(request):
            token = credentials.credentials
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing token")

        self.claims = await get_token_claims(token, ctx)

class JwtCookie(SecurityBase):
    def __init(self, *, auto_error: bool = True):
        self.auto_error = auto_error
        self.claims = None

    async def __call__(self, request: Request, response: Response, ctx: context.Context = Depends()):
        if not (access_token := request.cookies.get(ctx.config.security.cookie_access_token_name)):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing token")
        refresh_token = request.cookies.get(ctx.config.security.cookie_refresh_token_name)

        if ctx.config.oauth2.jwt_signing_algo in ["HS256", "HS384", "HS512"]:
            secret = ctx.config.oauth2.jwt_secret 
        else:
           secret = ctx.config.oauth2.jwt_signing_key

        try:
            refresh_claims = security.validate_token(refresh_token, secret) if refresh_token else None
            # TODO: check expiration
        except jwt.PyJWTError:
            refresh_claims = None 

        try:
            access_claims = security.validate_token(access_token, secret)
            # TODO: if exp then check refresh token and create new else raise
        except jwt.PyJWTError as e:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {e}")
        else: 
            # TODO: validate user
            pass

        self.claims = access_claims


WILDCARD = "*"
NULL = "null"

class HttpHeader(StrEnum):
    ACCESS_CONTROL_ALLOW_CREDENTIALS = "Access-Control-Allow-Credentials"
    ACCESS_CONTROL_ALLOW_METHODS = "Access-Control-Allow-Methods"
    ACCESS_CONTROL_ALLOW_ORIGIN = "Access-Control-Allow-Origin"
    ACCESS_CONTROL_ALLOW_HEADERS = "Access-Control-Allow-Headers"
    ACCESS_CONTROL_EXPOSE_HEADERS = "Access-Control-Expose-Headers"
    ACCESS_CONTROL_MAX_AGE = "Access-Control-Max-Age"
    CONTENT_TYPE = "Content-Type"
    AUTHORIZATION = "Authorization"
    VARY = "Vary"
    ORIGIN = "Origin"

class CorsMiddleware(BaseModel):
    allow_credentials: bool = False 
    allow_headers: Sequence[HttpHeader | str] = []
    allow_methods: Sequence[HttpMethod | str] = []
    allow_origin: str = WILDCARD
    expose_headers: Sequence[HttpHeader | str] = []
    max_age: int = 600


    async def __call__(self, request: Request, response: Response):

        response.headers[HttpHeader.ACCESS_CONTROL_ALLOW_CREDENTIALS] = str(self.allow_credentials).lower()
        response.headers[HttpHeader.ACCESS_CONTROL_ALLOW_HEADERS] = self.make_from(self.allow_headers)
        response.headers[HttpHeader.ACCESS_CONTROL_ALLOW_METHODS] = self.make_from(self.allow_methods)
        response.headers[HttpHeader.ACCESS_CONTROL_ALLOW_ORIGIN] = str(self.allow_origin)
        response.headers[HttpHeader.ACCESS_CONTROL_EXPOSE_HEADERS] = self.make_from(self.expose_headers)
        response.headers[HttpHeader.ACCESS_CONTROL_MAX_AGE] = str(self.max_age)

    def make_from(self, value: Sequence[HttpHeader | HttpMethod | str]) -> str:
        if WILDCARD in value:
            return WILDCARD
        elif NULL in value: 
            return NULL
        else:
            return ",".join(set(value))

