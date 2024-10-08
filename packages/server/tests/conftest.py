import pytest_asyncio
from materia_server.models import (
    User,
    LoginType,
)
from materia_server.models.base import Base
from materia_server import security
from materia_server.app import Application
from materia_server.core import Config, Database, Cache, Cron
import sqlalchemy as sa
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport, Cookies
from asgi_lifespan import LifespanManager
from pathlib import Path


@pytest_asyncio.fixture(scope="session")
async def config() -> Config:
    conf = Config()
    conf.database.port = 54320
    conf.cache.port = 63790

    return conf


@pytest_asyncio.fixture(scope="session")
async def database(config: Config) -> Database:
    config_postgres = config
    config_postgres.database.user = "postgres"
    config_postgres.database.name = "postgres"
    database_postgres = await Database.new(
        config_postgres.database.url(), poolclass=NullPool
    )

    async with database_postgres.connection() as connection:
        await connection.execution_options(isolation_level="AUTOCOMMIT")
        await connection.execute(sa.text("create role pytest login"))
        await connection.execute(sa.text("create database pytest owner pytest"))
        await connection.commit()

    await database_postgres.dispose()

    config.database.user = "pytest"
    config.database.name = "pytest"
    database_pytest = await Database.new(config.database.url(), poolclass=NullPool)

    yield database_pytest

    await database_pytest.dispose()

    async with database_postgres.connection() as connection:
        await connection.execution_options(isolation_level="AUTOCOMMIT")
        await connection.execute(sa.text("drop database pytest")),
        await connection.execute(sa.text("drop role pytest"))
        await connection.commit()
    await database_postgres.dispose()


@pytest_asyncio.fixture(scope="session")
async def cache(config: Config) -> Cache:
    config_pytest = config
    config_pytest.cache.user = "pytest"
    cache_pytest = await Cache.new(config_pytest.cache.url())

    yield cache_pytest


@pytest_asyncio.fixture(scope="session")
async def cron(config: Config) -> Cache:
    cron_pytest = Cron.new(
        config.cron.workers_count,
        backend_url=config.cache.url(),
        broker_url=config.cache.url(),
    )

    yield cron_pytest


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database(database: Database):
    async with database.connection() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.commit()
    yield
    async with database.connection() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.commit()


@pytest_asyncio.fixture()
async def session(database: Database, request):
    session = database.sessionmaker()
    yield session
    await session.rollback()
    await session.close()


@pytest_asyncio.fixture(scope="function")
async def data(config: Config):
    class TestData:
        user = User(
            name="PyTest",
            lower_name="pytest",
            email="pytest@example.com",
            hashed_password=security.hash_password(
                "iampytest", algo=config.security.password_hash_algo
            ),
            login_type=LoginType.Plain,
            is_admin=True,
        )

    return TestData()


@pytest_asyncio.fixture(scope="function")
async def api_config(config: Config, tmpdir) -> Config:
    config.application.working_directory = Path(tmpdir)
    config.oauth2.jwt_secret = "pytest_secret_key"

    yield config


@pytest_asyncio.fixture(scope="function")
async def api_client(
    api_config: Config, database: Database, cache: Cache, cron: Cron
) -> AsyncClient:

    app = Application(api_config)
    app.database = database
    app.cache = cache
    app.cron = cron
    app.prepare_server()

    async with LifespanManager(app.backend) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app), base_url=api_config.server.url()
        ) as client:
            yield client


@pytest_asyncio.fixture(scope="function")
async def auth_client(api_client: AsyncClient, api_config: Config) -> AsyncClient:
    data = {"name": "PyTest", "password": "iampytest", "email": "pytest@example.com"}

    await api_client.post(
        "/api/auth/signup",
        json=data,
    )
    auth = await api_client.post(
        "/api/auth/signin",
        json=data,
    )

    cookies = Cookies()
    cookies.set(
        "materia_at",
        auth.cookies[api_config.security.cookie_access_token_name],
    )
    cookies.set(
        "materia_rt",
        auth.cookies[api_config.security.cookie_refresh_token_name],
    )

    api_client.cookies = cookies

    yield api_client
