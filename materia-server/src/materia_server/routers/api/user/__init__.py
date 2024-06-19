from fastapi import APIRouter
from materia_server.routers.api.user import user

router = APIRouter() 
router.include_router(user.router)
