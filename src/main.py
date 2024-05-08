from contextlib import asynccontextmanager
from os import environ

import uvicorn
from fastapi import FastAPI

from src.config import config
from src.db import DatabaseManager


@asynccontextmanager 
async def lifespan(app: FastAPI):
    pool = DatabaseManager.from_url(config.database_url()) # type: ignore

    app.state.config = config
    app.state.pool = pool
    
    async with pool.connection() as connection:
        await connection.run_sync(pool.run_migrations) # type: ignore

    yield

    if pool.engine is not None:
        await pool.dispose()


app = FastAPI(
    title = "materia",
    version = "0.1.0",
    docs_url = "/api/docs",
    lifespan = lifespan
)

def main():
    uvicorn.run(
        "src.main:app", 
        port = config.server.port, 
        host = config.server.address, 
        reload = bool(environ.get("MATERIA_DEBUG"))
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass



