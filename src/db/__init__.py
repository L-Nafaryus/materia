from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from alembic.config import Config
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from alembic.script.base import ScriptDirectory
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base 
from asyncpg import Connection


class DatabaseManager:
    def __init__(self):
        self.engine: AsyncEngine | None = None 
        self.sessionmaker: async_sessionmaker[AsyncSession] | None = None 
        self.database_url: str | None = None

    @staticmethod
    def from_url(database_url: str):
        instance = DatabaseManager()
        instance.database_url = database_url
        instance.engine = create_async_engine(database_url, pool_size = 100)
        instance.sessionmaker = async_sessionmaker(bind = instance.engine, autocommit = False, autoflush = False)

        return instance

    async def dispose(self):
        if self.engine is None:
            raise Exception("DatabaseManager engine is not initialized")

        await self.engine.dispose()
        self.database_url = None
        self.engine = None 
        self.sessionmaker = None

    @asynccontextmanager 
    async def connection(self) -> AsyncIterator[AsyncConnection]:
        if self.engine is None:
            raise Exception("DatabaseManager engine is not initialized")

        async with self.engine.begin() as connection:
            try:
                yield connection 
            except Exception as e:
                await connection.rollback()
                raise e 

    @asynccontextmanager 
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self.sessionmaker is None:
            raise Exception("DatabaseManager session is not initialized")

        session = self.sessionmaker();
        try:
            yield session 
        except Exception as e:
            await session.rollback()
            raise e 
        finally:
            await session.close()

    def run_migrations(self, connection: Connection):
        if self.engine is None:
            raise Exception("DatabaseManager engine is not initialized")

        config = Config(Path("alembic.ini"))
        config.set_main_option("sqlalchemy.url", self.database_url) # type: ignore

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


Base = declarative_base()

from src.db.user import User

