from fastapi import APIRouter, HTTPException
from materia.routers.api.auth import auth, oauth
from materia.routers.api import docs, user, repository, directory, file

router = APIRouter(prefix="/api")
router.include_router(docs.router)
router.include_router(auth.router)
router.include_router(oauth.router)
router.include_router(user.router)
router.include_router(repository.router)
router.include_router(directory.router)
router.include_router(file.router)


@router.get("/api/{catchall:path}", status_code=404, include_in_schema=False)
def not_found():
    raise HTTPException(status_code=404)
