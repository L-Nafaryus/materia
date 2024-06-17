from typing import Optional, Sequence
import uuid
from fastapi import HTTPException, Request, Response, status, Depends
import jwt
from sqlalchemy import select 
from pydantic import BaseModel
from enum import StrEnum
from http import HTTPMethod as HttpMethod
from fastapi.security import HTTPBearer, OAuth2PasswordBearer, OAuth2PasswordRequestForm, APIKeyQuery, APIKeyCookie, APIKeyHeader

from materia.api.state import ConfigState, DatabaseState
from materia.api.token import TokenClaims
from materia import db


class JwtMiddleware(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error = auto_error)
        self.claims: Optional[TokenClaims] = None 

    async def __call__(self, request: Request, config: ConfigState = Depends(), database: DatabaseState = Depends()):
        if token := request.cookies.get("token"):
            pass 
        elif (credentials := await super().__call__(request)) and credentials.scheme == "Bearer":
            token = credentials.credentials

        if not token:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing token")

        try:
            self.claims = TokenClaims.verify(token, config.jwt.secret)
            user_id = uuid.UUID(self.claims.sub) # type: ignore
        except jwt.PyJWKError as _:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
        except ValueError as _:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid token")

        async with database.session() as session:
            if not (user := (await session.scalars(select(db.User).where(db.User.id == user_id))).first()):
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing user")

        request.state.user = user

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

