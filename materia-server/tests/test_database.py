import pytest_asyncio
import pytest
import os
from materia_server.config import Config
from materia_server.models import Database, User, LoginType, Repository, Directory
from materia_server import security
import sqlalchemy as sa
from sqlalchemy.pool import NullPool
from dataclasses import dataclass


@pytest_asyncio.fixture(scope="session")
async def config() -> Config:
    conf = Config()
    conf.database.port = 54320
    # conf.application.working_directory = conf.application.working_directory / "temp"
    # if (cwd := conf.application.working_directory.resolve()).exists():
    #    os.chdir(cwd)
    # if local_conf := Config.open(cwd / "config.toml"):
    #    conf = local_conf
    return conf


@pytest_asyncio.fixture(scope="session")
async def db(config: Config, request) -> Database:
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
    database = await Database.new(config.database.url(), poolclass=NullPool)

    yield database

    await database.dispose()

    # database_postgres = await Database.new(config_postgres.database.url())
    async with database_postgres.connection() as connection:
        await connection.execution_options(isolation_level="AUTOCOMMIT")
        await connection.execute(sa.text("drop database pytest")),
        await connection.execute(sa.text("drop role pytest"))
        await connection.commit()
    await database_postgres.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db(db: Database, request):
    await db.run_migrations()
    yield
    # await db.rollback_migrations()


@pytest_asyncio.fixture(autouse=True)
async def session(db: Database, request):
    session = db.sessionmaker()
    yield session
    await session.rollback()
    await session.close()


@pytest_asyncio.fixture(scope="session")
async def user(config: Config, session) -> User:
    test_user = User(
        name="pytest",
        lower_name="pytest",
        email="pytest@example.com",
        hashed_password=security.hash_password(
            "iampytest", algo=config.security.password_hash_algo
        ),
        login_type=LoginType.Plain,
        is_admin=True,
    )

    async with db.session() as session:
        session.add(test_user)
        await session.flush()
        await session.refresh(test_user)

    yield test_user

    async with db.session() as session:
        await session.delete(test_user)
        await session.flush()


@pytest_asyncio.fixture
async def data(config: Config):
    class TestData:
        user = User(
            name="pytest",
            lower_name="pytest",
            email="pytest@example.com",
            hashed_password=security.hash_password(
                "iampytest", algo=config.security.password_hash_algo
            ),
            login_type=LoginType.Plain,
            is_admin=True,
        )

    return TestData()


@pytest.mark.asyncio
async def test_user(data, session):
    session.add(data.user)
    await session.flush()

    assert data.user.id is not None
    assert security.validate_password("iampytest", data.user.hashed_password)


@pytest.mark.asyncio
async def test_repository(data, session, config):
    session.add(data.user)
    await session.flush()

    repository = Repository(user_id=data.user.id, capacity=config.repository.capacity)
    session.add(repository)
    await session.flush()

    assert repository.id is not None


@pytest.mark.asyncio
async def test_directory(data, session, config):
    session.add(data.user)
    await session.flush()

    repository = Repository(user_id=data.user.id, capacity=config.repository.capacity)
    session.add(repository)
    await session.flush()

    directory = Directory(
        repository_id=repository.id, parent_id=None, name="test1", path=None
    )
    session.add(directory)
    await session.flush()

    assert directory.id is not None
    assert (
        await session.scalars(
            sa.select(Directory).where(
                sa.and_(
                    Directory.repository_id == repository.id,
                    Directory.name == "test1",
                    Directory.path.is_(None),
                )
            )
        )
    ).first() == directory

    nested_directory = Directory(
        repository_id=repository.id,
        parent_id=directory.id,
        name="test_nested",
        path="test1",
    )
    session.add(nested_directory)
    await session.flush()

    assert nested_directory.id is not None
    assert (
        await session.scalars(
            sa.select(Directory).where(
                sa.and_(
                    Directory.repository_id == repository.id,
                    Directory.name == "test_nested",
                    Directory.path == "test1",
                )
            )
        )
    ).first() == nested_directory
    assert nested_directory.parent_id == directory.id
