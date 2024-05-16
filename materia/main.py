from contextlib import asynccontextmanager
from os import environ

import uvicorn
from fastapi import FastAPI

from materia.config import config
from materia.db import DatabaseManager
from materia import api


@asynccontextmanager 
async def lifespan(app: FastAPI):
    database = DatabaseManager.from_url(config.database_url()) # type: ignore

    app.state.config = config
    app.state.database = database
    
    async with database.connection() as connection:
        await connection.run_sync(database.run_migrations) # type: ignore

    yield

    if database.engine is not None:
        await database.dispose()


app = FastAPI(
    title = "materia",
    version = "0.1.0",
    docs_url = "/api/docs",
    lifespan = lifespan
)
app.include_router(api.routes())

def main():
    uvicorn.run(
        "materia.main:app", 
        port = config.server.port, 
        host = config.server.address, 
        reload = bool(environ.get("MATERIA_DEBUG"))
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass



