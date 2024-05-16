from fastapi import APIRouter
from materia.api import user 

def routes() -> APIRouter:
    router = APIRouter(prefix = "/api")

    router.include_router(user.router)

    return router
