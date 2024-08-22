import pytest_asyncio
import pytest
from pathlib import Path
from materia.config import Config
from materia.models import (
    User,
    Repository,
    Directory,
    RepositoryError,
    File,
)
from materia.models.database import SessionContext
from materia import security
import sqlalchemy as sa
from sqlalchemy.orm.session import make_transient
from sqlalchemy import inspect
import aiofiles
import aiofiles.os


@pytest.mark.asyncio
async def test_user(data, session: SessionContext, config: Config):
    # simple
    session.add(data.user)
    await session.flush()

    assert data.user.id is not None
    assert security.validate_password("iampytest", data.user.hashed_password)

    await session.rollback()

    # methods
    await data.user.new(session, config)

    assert data.user.id is not None
    assert await data.user.count(session) == 1
    assert await User.by_name("PyTest", session) == data.user
    assert await User.by_email("pytest@example.com", session) == data.user

    await data.user.edit_name("AsyncPyTest", session)
    assert await User.by_name("asyncpytest", session, with_lower=True) == data.user
    assert await User.by_email("pytest@example.com", session) == data.user
    assert await User.by_id(data.user.id, session) == data.user
    await data.user.edit_password("iamnotpytest", session, config)
    assert security.validate_password("iamnotpytest", data.user.hashed_password)

    await data.user.remove(session)


@pytest.mark.asyncio
async def test_repository(data, tmpdir, session: SessionContext, config: Config):
    config.application.working_directory = Path(tmpdir)

    session.add(data.user)
    await session.flush()

    repository = await Repository(
        user_id=data.user.id, capacity=config.repository.capacity
    ).new(session, config)

    assert repository
    assert repository.id is not None
    assert (await repository.real_path(session, config)).exists()
    assert await Repository.from_user(data.user, session) == repository

    await session.refresh(repository, attribute_names=["user"])
    cloned_repository = repository.clone()
    assert cloned_repository.id is None and cloned_repository.user is None
    session.add(cloned_repository)
    await session.flush()
    assert cloned_repository.id is not None

    await repository.remove(session, config)
    make_transient(repository)
    session.add(repository)
    await session.flush()
    with pytest.raises(RepositoryError):
        await repository.remove(session, config)
    assert not (await repository.real_path(session, config)).exists()


@pytest.mark.asyncio
async def test_directory(data, tmpdir, session: SessionContext, config: Config):
    config.application.working_directory = Path(tmpdir)

    # setup
    session.add(data.user)
    await session.flush()

    repository = await Repository(
        user_id=data.user.id, capacity=config.repository.capacity
    ).new(session, config)

    directory = await Directory(
        repository_id=repository.id, parent_id=None, name="test1"
    ).new(session, config)

    # simple
    assert directory.id is not None
    assert (
        await session.scalars(
            sa.select(Directory).where(
                sa.and_(
                    Directory.repository_id == repository.id,
                    Directory.name == "test1",
                )
            )
        )
    ).first() == directory
    assert (await directory.real_path(session, config)).exists()

    # nested simple
    nested_directory = await Directory(
        repository_id=repository.id,
        parent_id=directory.id,
        name="test_nested",
    ).new(session, config)

    assert nested_directory.id is not None
    assert (
        await session.scalars(
            sa.select(Directory).where(
                sa.and_(
                    Directory.repository_id == repository.id,
                    Directory.name == "test_nested",
                )
            )
        )
    ).first() == nested_directory
    assert nested_directory.parent_id == directory.id
    assert (await nested_directory.real_path(session, config)).exists()

    # relationship
    await session.refresh(directory, attribute_names=["directories", "files"])
    assert isinstance(directory.files, list) and len(directory.files) == 0
    assert isinstance(directory.directories, list) and len(directory.directories) == 1

    await session.refresh(nested_directory, attribute_names=["directories", "files"])
    assert (nested_directory.files, list) and len(nested_directory.files) == 0
    assert (nested_directory.directories, list) and len(
        nested_directory.directories
    ) == 0

    #
    assert (
        await Directory.by_path(
            repository, Path("test1", "test_nested"), session, config
        )
        == nested_directory
    )

    # remove nested
    nested_path = await nested_directory.real_path(session, config)
    assert nested_path.exists()
    await nested_directory.remove(session, config)
    assert inspect(nested_directory).was_deleted
    assert await nested_directory.real_path(session, config) is None
    assert not nested_path.exists()

    await session.refresh(directory)  # update attributes that was deleted
    assert (await directory.real_path(session, config)).exists()

    # rename
    assert (
        await directory.rename("test1", session, config, force=True)
    ).name == "test1.1"
    await Directory(repository_id=repository.id, parent_id=None, name="test2").new(
        session, config
    )
    assert (
        await directory.rename("test2", session, config, force=True)
    ).name == "test2.1"
    assert (await repository.real_path(session, config)).joinpath("test2.1").exists()
    assert not (await repository.real_path(session, config)).joinpath("test1").exists()

    directory_path = await directory.real_path(session, config)
    assert directory_path.exists()

    await directory.remove(session, config)
    assert await directory.real_path(session, config) is None
    assert not directory_path.exists()


@pytest.mark.asyncio
async def test_file(data, tmpdir, session: SessionContext, config: Config):
    config.application.working_directory = Path(tmpdir)

    # setup
    session.add(data.user)
    await session.flush()

    repository = await Repository(
        user_id=data.user.id, capacity=config.repository.capacity
    ).new(session, config)

    directory = await Directory(
        repository_id=repository.id, parent_id=None, name="test1"
    ).new(session, config)
    directory2 = await Directory(
        repository_id=repository.id, parent_id=None, name="test2"
    ).new(session, config)

    data = b"Hello there, it's a test"
    file = await File(
        repository_id=repository.id,
        parent_id=directory.id,
        name="test_file.txt",
    ).new(data, session, config)

    # simple
    assert file.id is not None
    assert (
        await session.scalars(
            sa.select(File).where(
                sa.and_(
                    File.repository_id == repository.id,
                    File.parent_id == directory.id,
                    File.name == "test_file.txt",
                )
            )
        )
    ).first() == file

    # relationship
    await session.refresh(file, attribute_names=["parent", "repository"])
    assert file.parent == directory
    assert file.repository == repository

    #
    assert (
        await File.by_path(repository, Path("test1", "test_file.txt"), session, config)
        == file
    )

    #
    file_path = await file.real_path(session, config)
    assert file_path.exists()
    assert (await aiofiles.os.stat(file_path)).st_size == file.size
    async with aiofiles.open(file_path, mode="rb") as io:
        content = await io.read()
    assert data == content

    # rename
    assert (
        await file.rename("test_file_rename.txt", session, config, force=True)
    ).name == "test_file_rename.txt"
    await File(
        repository_id=repository.id, parent_id=directory.id, name="test_file_2.txt"
    ).new(b"", session, config)
    assert (
        await file.rename("test_file_2.txt", session, config, force=True)
    ).name == "test_file_2.1.txt"
    assert (
        (await repository.real_path(session, config))
        .joinpath("test1", "test_file_2.1.txt")
        .exists()
    )
    assert (
        not (await repository.real_path(session, config))
        .joinpath("test1", "test_file_rename.txt")
        .exists()
    )

    # move
    await file.move(directory2, session, config)
    await session.refresh(file, attribute_names=["parent"])
    assert file.parent == directory2
    assert (
        not (await repository.real_path(session, config))
        .joinpath("test1", "test_file_2.1.txt")
        .exists()
    )
    assert (
        (await repository.real_path(session, config))
        .joinpath("test2", "test_file_2.1.txt")
        .exists()
    )

    # remove
    await file.remove(session, config)
    assert not await File.by_path(
        repository, Path("test1", "test_file.txt"), session, config
    )
    assert not file_path.exists()
