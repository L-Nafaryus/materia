from fastapi import APIRouter, HTTPException
from materia_server.routers.api.auth import auth, oauth
from materia_server.routers.api import docs, user, repository, directory, file, avatar

router = APIRouter(prefix="/api")
router.include_router(docs.router)
router.include_router(auth.router)
router.include_router(oauth.router)
router.include_router(user.router)
router.include_router(repository.router)
router.include_router(directory.router)
router.include_router(file.router)
router.include_router(avatar.router)


@router.get("/api/{catchall:path}", status_code=404, include_in_schema=False)
def not_found():
    raise HTTPException(status_code=404)
