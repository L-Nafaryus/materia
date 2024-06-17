import os
import time
from pathlib import Path
from typing import Annotated
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordRequestFormStrict
import httpx
from sqlalchemy import and_, insert, select, update
from authlib.integrations.starlette_client import OAuth, OAuthError
import base64 
from cryptography.fernet import Fernet
import json

from materia import db
from materia.api import schema
from materia.api.state import ConfigState, DatabaseState
from materia.api.middleware import JwtMiddleware
from materia.api.token import TokenClaims
from materia.config import Config

oauth = OAuth()
oauth.register(
    "materia", 
    authorize_url = "http://127.0.0.1:54601/api/auth/authorize",
    access_token_url = "http://127.0.0.1:54601/api/auth/token",
    scope = "user:read",
    client_id = "",
    client_secret = ""
)

class OAuth2Provider:
    pass

router = APIRouter(tags = ["auth"])

@router.get("/user/signin")
async def signin(request: Request, provider: str = None):
    if not provider:
        return RedirectResponse("/api/auth/authorize")
    else:
        return RedirectResponse(request.url_for(provider.authorize_url))

@router.post("/auth/test_auth")
async def test_auth(database: DatabaseState = Depends()):
    async with httpx.AsyncClient() as client:
        response = await client.post("https://vcs.elnafo.ru/login/oauth/authorize", data = {
            "client_id": "1edfe-0bbe-4f53-bab6-7e24f0b842e3", 
            "client_secret": "gto_7ecfnqg2c6kbe2qf25wjee237mmkxvbkb7arjacyvtypi24hqv4q",
            "response_type": "code", 
            "redirect_uri": "http://127.0.0.1:54601"
        })
        return response.content, response.status_code

@router.post("/auth/provider")
async def provider(form: Annotated[OAuth2PasswordRequestForm, Depends()], database: DatabaseState = Depends()):
    async with httpx.AsyncClient() as client:
        response = await client.post("https://vcs.elnafo.ru/login/oauth/access_token", data = {
            "client_id": "1edfec03-0bbe-4f53-bab6-7e24f0b842e3", 
            "client_secret": "gto_7ecfnqg2c6kbe2qf25wjee237mmkxvbkb7arjacyvtypi24hqv4q",
            "grant_type": "authorization_code",
            "code": "gta_63l6zogw5wlnkeng4gf3buqtoekkaxk7zhr67zlkyrv2ukwfeava"
        })
        return response.content, response.status_code

@router.post("/auth/authorize")
async def authorize(form: Annotated[OAuth2PasswordRequestForm, Depends()], database: DatabaseState = Depends()):


    if form.client_id:
        async with database.session() as session:
            if not (user := (await session.scalars(select(db.User).where(db.User.login_name == form.username))).first()):
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid user") 

            await session.refresh(user, attribute_names = ["oauth2_apps"])
            oauth2_app = None 

            for app in user.oauth2_apps:
                if form.client_id == app.client_id and bcrypt.checkpw(form.client_secret.encode(), app.client_secret):
                    oauth2_app = app 

            if not oauth2_app:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid client id")

        data = json.dumps({"client_id": form.client_id}).encode()

    else:
        async with database.session() as session:
            if not (user := (await session.scalars(select(db.User).where(db.User.login_name == form.username))).first()):
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid user credentials")

        if not bcrypt.checkpw(form.password.encode(), user.hashed_password.encode()):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid password")

        data = json.dumps({"username": form.username}).encode()

    key = b'sGEuUeKrooiNAy7L9sf6IFIjpv86TC9iYU_sbWqA-1c=' # Fernet.generate_key()
    f = Fernet(key)
    code = base64.b64encode(f.encrypt(data), b"-_").decode().replace("=", "")
    global storage
    storage = code
    return code

storage = None


@router.post("/auth/token")
async def token(exchange: schema.Exchange, response: Response, config: ConfigState = Depends()):
    if exchange.grant_type == "authorization_code":
        if not exchange.code:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Missing authorization code")
        # expiration
        if exchange.code != storage:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Invalid authorization code")

        token = TokenClaims.create(
            "asd",
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

        return schema.AccessToken(  
            access_token = token, 
            token_type = "Bearer", 
            expires_in = config.jwt.maxage, 
            refresh_token = token, 
            scope = "identify"
        )
    elif exchange.grant_type == "refresh_token":
        pass
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
