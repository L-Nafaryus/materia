

from typing import Annotated, Optional, Union
from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.security import OAuth2PasswordRequestFormStrict, SecurityScopes
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from pydantic import BaseModel, HttpUrl
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from materia_server.models import User
from materia_server.routers.middleware import Context


router = APIRouter(tags = ["oauth2"])

class OAuth2AuthorizationCodeRequestForm:
    def __init__(
        self, 
        redirect_uri: Annotated[HttpUrl, Form()],
        client_id: Annotated[str, Form()],
        scope: Annotated[Union[str, None], Form()] = None,
        state: Annotated[Union[str, None], Form()] = None,
        response_type: Annotated[str, Form()] = "code",
        grant_type: Annotated[str, Form(pattern = "password")] = "authorization_code"
    ) -> None:
        self.redirect_uri = redirect_uri 
        self.client_id = client_id
        self.scope = scope
        self.state = state
        self.response_type = response_type
        self.grant_type = grant_type

class AuthorizationCodeResponse(BaseModel):
    code: str

@router.post("/oauth2/authorize")
async def authorize(form: Annotated[OAuth2AuthorizationCodeRequestForm, Depends()], ctx: Context = Depends()):
    # grant_type: authorization_code, password_credentials, client_credentials, authorization_code (pkce)
    ctx.logger.debug(form)

    if form.grant_type == "authorization_code":
        # TODO: form validation 

        if not (app := await OAuth2Application.by_client_id(form.client_id, ctx.database)):
            raise HTTPException(status_code = HTTP_500_INTERNAL_SERVER_ERROR, detail = "Client ID not registered")

        if not (owner := await User.by_id(app.user_id, ctx.database)):
            raise HTTPException(status_code = HTTP_500_INTERNAL_SERVER_ERROR, detail = "User not found")

        if not app.contains_redirect_uri(form.redirect_uri):
            raise HTTPException(status_code = HTTP_500_INTERNAL_SERVER_ERROR, detail = "Unregistered redirect URI")

        if not form.response_type == "code":
            raise HTTPException(status_code = HTTP_500_INTERNAL_SERVER_ERROR, detail = "Unsupported response type")

        # TODO: code challenge (S256, plain, ...)
        # None: if not app.confidential_client: raise ...

        grant = await app.grant_by_user_id(owner.id, ctx.database)

        if app.confidential_client and grant is not None:
            code = await grant.generate_authorization_code(form.redirect_uri, ctx.cache)
            # TODO: include state to redirect_uri

            # return redirect 

        # redirect to grant page
    else:
        raise HTTPException(status_code = HTTP_500_INTERNAL_SERVER_ERROR, detail = "Unsupported grant type")

    pass 

class AccessTokenResponse(BaseModel):
    access_token: str 
    token_type: str 
    expires_in: int 
    refresh_token: str
    scope: Optional[str]

@router.post("/oauth2/access_token")
async def token(ctx: Context = Depends()):
    pass
