
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from materia_server import security
from materia_server.routers import context
from materia_server.models import user
from materia_server.models import auth
from materia_server.routers.middleware import JwtMiddleware

router = APIRouter(tags = ["user"])

@router.get("/user/identity", response_model = user.UserIdentity)
async def identity(request: Request, claims = Depends(JwtMiddleware()), ctx: context.Context = Depends()):
    if not (current_user := await user.User.by_id(uuid.UUID(claims.sub), ctx.database)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing user")

    return user.UserIdentity.model_validate(current_user)
