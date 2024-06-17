from contextlib import asynccontextmanager
from typing import AsyncIterator, Self
from pathlib import Path

from pydantic import BaseModel, PostgresDsn
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from asyncpg import Connection
from alembic.config import Config as AlembicConfig
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from alembic.script.base import ScriptDirectory

from materia_server.models.base import Base

__all__ = [ "Database" ]

class Database:
    def __init__(self, url: PostgresDsn, engine: AsyncEngine, sessionmaker: async_sessionmaker[AsyncSession]):
        self.url: PostgresDsn = url 
        self.engine: AsyncEngine = engine
        self.sessionmaker: async_sessionmaker[AsyncSession] = sessionmaker

    @staticmethod
    def new(url: PostgresDsn, pool_size: int = 100, autocommit: bool = False, autoflush: bool = False, expire_on_commit: bool = False) -> Self:
        engine = create_async_engine(str(url), pool_size = pool_size)
        sessionmaker = async_sessionmaker(
            bind = engine,
            autocommit = autocommit,
            autoflush = autoflush,
            expire_on_commit = expire_on_commit
        )

        return Database(
            url = url,
            engine = engine,
            sessionmaker = sessionmaker
        )

    async def dispose(self):
        await self.engine.dispose()

    @asynccontextmanager 
    async def connection(self) -> AsyncIterator[AsyncConnection]:
        async with self.engine.begin() as connection:
            try:
                yield connection 
            except Exception as e:
                await connection.rollback()
                raise e 

    @asynccontextmanager 
    async def session(self) -> AsyncIterator[AsyncSession]:
        session = self.sessionmaker();

        try:
            yield session 
        except Exception as e:
            await session.rollback()
            raise e 
        finally:
            await session.close()

    def run_migrations(self, connection: Connection):
        config = AlembicConfig(Path(__file__).parent.parent.parent / "alembic.ini")
        config.set_main_option("sqlalchemy.url", self.url) # type: ignore

        context = MigrationContext.configure(
            connection = connection, # type: ignore
            opts = {
                "target_metadata": Base.metadata,
                "fn": lambda rev, _: ScriptDirectory.from_config(config)._upgrade_revs("head", rev)
            }
        )
        
        with context.begin_transaction():
            with Operations.context(context):
                context.run_migrations()

  
