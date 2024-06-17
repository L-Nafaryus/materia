from fastapi import APIRouter
from materia_server.routers.api import auth 

router = APIRouter(prefix = "/api")

router.include_router(auth.router)
