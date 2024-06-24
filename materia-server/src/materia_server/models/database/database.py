from contextlib import asynccontextmanager
import os
from typing import AsyncIterator, Self
from pathlib import Path

from pydantic import BaseModel, PostgresDsn
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from asyncpg import Connection
from alembic.config import Config as AlembicConfig
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from alembic.script.base import ScriptDirectory

from materia_server.config import Config
from materia_server.models.base import Base

__all__ = [ "Database" ]

class DatabaseError(Exception):
    pass

class DatabaseMigrationError(Exception):
    pass

class Database:
    def __init__(self, url: PostgresDsn, engine: AsyncEngine, sessionmaker: async_sessionmaker[AsyncSession]):
        self.url: PostgresDsn = url 
        self.engine: AsyncEngine = engine
        self.sessionmaker: async_sessionmaker[AsyncSession] = sessionmaker

    @staticmethod
    async def new(
            url: PostgresDsn, 
            pool_size: int = 100, 
            autocommit: bool = False, 
            autoflush: bool = False, 
            expire_on_commit: bool = False,
            test_connection: bool = True
        ) -> Self:
        engine = create_async_engine(str(url), pool_size = pool_size)
        sessionmaker = async_sessionmaker(
            bind = engine,
            autocommit = autocommit,
            autoflush = autoflush,
            expire_on_commit = expire_on_commit
        )

        database = Database(
            url = url,
            engine = engine,
            sessionmaker = sessionmaker
        )

        if test_connection:
            try:
                async with database.connection() as connection:
                    await connection.rollback()
            except Exception as e:
                raise DatabaseError(f"{e}")

        return database

    async def dispose(self):
        await self.engine.dispose()

    @asynccontextmanager 
    async def connection(self) -> AsyncIterator[AsyncConnection]:
        async with self.engine.begin() as connection:
            try:
                yield connection 
            except Exception as e:
                await connection.rollback()
                raise DatabaseError(f"{e}") 

    @asynccontextmanager 
    async def session(self) -> AsyncIterator[AsyncSession]:
        session = self.sessionmaker();

        try:
            yield session 
        except Exception as e:
            await session.rollback()
            raise DatabaseError(f"{e}") 
        finally:
            await session.close()

    def run_sync_migrations(self, connection: Connection):
        aconfig = AlembicConfig() 
        aconfig.set_main_option("sqlalchemy.url", str(self.url))
        aconfig.set_main_option("script_location", str(Path(__file__).parent.parent.joinpath("migrations")))

        context = MigrationContext.configure(
            connection = connection, # type: ignore
            opts = {
                "target_metadata": Base.metadata,
                "fn": lambda rev, _: ScriptDirectory.from_config(aconfig)._upgrade_revs("head", rev)
            }
        )

        try:
            with context.begin_transaction():
                with Operations.context(context):
                    context.run_migrations()
        except Exception as e:
            raise DatabaseMigrationError(f"{e}")

    async def run_migrations(self):
        async with self.connection() as connection:
            await connection.run_sync(self.run_sync_migrations) # type: ignore
  
