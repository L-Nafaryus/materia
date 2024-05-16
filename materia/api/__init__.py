from fastapi import APIRouter
from materia.api import user, filesystem 

def routes() -> APIRouter:
    router = APIRouter(prefix = "/api")

    router.include_router(user.router)
    router.include_router(filesystem.router)

    return router
