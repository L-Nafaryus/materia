from fastapi import APIRouter
from materia_server.routers.api import auth 
from materia_server.routers.api import user

router = APIRouter(prefix = "/api")

router.include_router(auth.router)
router.include_router(user.router)
