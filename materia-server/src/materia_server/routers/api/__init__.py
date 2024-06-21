from fastapi import APIRouter
from materia_server.routers.api.auth import auth, oauth
from materia_server.routers.api import user, repository, directory

router = APIRouter() 
router.include_router(auth.router)
router.include_router(oauth.router)
router.include_router(user.router)
router.include_router(repository.router)
router.include_router(directory.router)
