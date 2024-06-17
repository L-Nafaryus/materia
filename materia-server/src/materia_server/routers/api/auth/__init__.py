from fastapi import APIRouter
from materia_server.routers.api.auth import auth
from materia_server.routers.api.auth import oauth

router = APIRouter() 
router.include_router(auth.router)
router.include_router(oauth.router)

