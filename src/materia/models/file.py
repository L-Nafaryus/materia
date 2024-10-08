from time import time
from typing import Optional, Self, Union
from pathlib import Path

from sqlalchemy import BigInteger, ForeignKey, inspect
from sqlalchemy.orm import mapped_column, Mapped, relationship
import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict

from materia.models.base import Base
from materia.core import SessionContext, Config, FileSystem


class FileError(Exception):
    pass


class File(Base):
    __tablename__ = "file"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repository.id", ondelete="CASCADE")
    )
    parent_id: Mapped[int] = mapped_column(
        ForeignKey("directory.id", ondelete="CASCADE"), nullable=True
    )
    created: Mapped[int] = mapped_column(BigInteger, nullable=False, default=time)
    updated: Mapped[int] = mapped_column(BigInteger, nullable=False, default=time)
    name: Mapped[str]
    is_public: Mapped[bool] = mapped_column(default=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=True)

    repository: Mapped["Repository"] = relationship(back_populates="files")
    parent: Mapped["Directory"] = relationship(back_populates="files")
    link: Mapped["FileLink"] = relationship(back_populates="file")

    async def new(
        self, data: Union[bytes, Path], session: SessionContext, config: Config
    ) -> Optional[Self]:
        session.add(self)
        await session.flush()
        await session.refresh(self, attribute_names=["repository"])

        file_path = await self.real_path(session, config)
        repository_path = await self.repository.real_path(session, config)
        new_file = FileSystem(file_path, repository_path)

        if isinstance(data, bytes):
            await new_file.write_file(data)
        elif isinstance(data, Path):
            from_file = FileSystem(data, config.application.working_directory)
            await from_file.move(file_path.parent, new_name=file_path.name)
        else:
            raise FileError(f"Unknown data type passed: {type(data)}")

        self.size = await new_file.size()
        await session.flush()

        return self

    async def remove(self, session: SessionContext, config: Config):
        session.add(self)

        file_path = await self.real_path(session, config)

        new_file = FileSystem(
            file_path, await self.repository.real_path(session, config)
        )
        await new_file.remove()

        await session.delete(self)
        await session.flush()

    async def relative_path(self, session: SessionContext) -> Optional[Path]:
        if inspect(self).was_deleted:
            return None

        file_path = Path()

        async with session.begin_nested():
            session.add(self)
            await session.refresh(self, attribute_names=["parent"])

            if self.parent:
                file_path = await self.parent.relative_path(session)

        return file_path.joinpath(self.name)

    async def real_path(
        self, session: SessionContext, config: Config
    ) -> Optional[Path]:
        if inspect(self).was_deleted:
            return None

        file_path = Path()

        async with session.begin_nested():
            session.add(self)
            await session.refresh(self, attribute_names=["repository", "parent"])

            if self.parent:
                file_path = await self.parent.real_path(session, config)
            else:
                file_path = await self.repository.real_path(session, config)

        return file_path.joinpath(self.name)

    @staticmethod
    async def by_path(
        repository: "Repository", path: Path, session: SessionContext, config: Config
    ) -> Optional[Self]:
        if path == Path():
            raise FileError("Cannot find file by empty path")

        parent_directory = (
            None
            if path.parent == Path()
            else await Directory.by_path(repository, path.parent, session, config)
        )

        current_file = (
            await session.scalars(
                sa.select(File).where(
                    sa.and_(
                        File.repository_id == repository.id,
                        File.name == path.name,
                        (
                            File.parent_id == parent_directory.id
                            if parent_directory
                            else File.parent_id.is_(None)
                        ),
                    )
                )
            )
        ).first()

        return current_file

    async def copy(
        self,
        directory: Optional["Directory"],
        session: SessionContext,
        config: Config,
        force: bool = False,
        shallow: bool = False,
    ) -> Self:
        session.add(self)
        await session.refresh(self, attribute_names=["repository"])

        repository_path = await self.repository.real_path(session, config)
        file_path = await self.real_path(session, config)
        directory_path = (
            await directory.real_path(session, config) if directory else repository_path
        )

        current_file = FileSystem(file_path, repository_path)
        new_file = await current_file.copy(directory_path, force=force, shallow=shallow)

        cloned = self.clone()
        cloned.name = new_file.name()
        cloned.parent_id = directory.id if directory else None
        session.add(cloned)
        await session.flush()

        return self

    async def move(
        self,
        directory: Optional["Directory"],
        session: SessionContext,
        config: Config,
        force: bool = False,
        shallow: bool = False,
    ) -> Self:
        session.add(self)
        await session.refresh(self, attribute_names=["repository"])

        repository_path = await self.repository.real_path(session, config)
        file_path = await self.real_path(session, config)
        directory_path = (
            await directory.real_path(session, config) if directory else repository_path
        )

        current_file = FileSystem(file_path, repository_path)
        moved_file = await current_file.move(
            directory_path, force=force, shallow=shallow
        )

        self.name = moved_file.name()
        self.parent_id = directory.id if directory else None
        self.updated = time()
        await session.flush()

        return self

    async def rename(
        self,
        name: str,
        session: SessionContext,
        config: Config,
        force: bool = False,
        shallow: bool = False,
    ) -> Self:
        session.add(self)
        await session.refresh(self, attribute_names=["repository"])

        repository_path = await self.repository.real_path(session, config)
        file_path = await self.real_path(session, config)

        current_file = FileSystem(file_path, repository_path)
        renamed_file = await current_file.rename(name, force=force, shallow=shallow)

        self.name = renamed_file.name()
        self.updated = time()
        await session.flush()
        return self

    async def info(self, session: SessionContext) -> Optional["FileInfo"]:
        info = FileInfo.model_validate(self)
        relative_path = await self.relative_path(session)
        info.path = Path("/").joinpath(relative_path) if relative_path else None

        return info


def convert_bytes(size: int):
    for unit in ["bytes", "kB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size}{unit}" if unit == "bytes" else f"{size:.1f}{unit}"
        size >>= 10


class FileLink(Base):
    __tablename__ = "file_link"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("file.id", ondelete="CASCADE"))
    created: Mapped[int] = mapped_column(BigInteger, default=time)
    url: Mapped[str]

    file: Mapped["File"] = relationship(back_populates="link")


class FileInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_id: int
    parent_id: Optional[int]
    created: int
    updated: int
    name: str
    is_public: bool
    size: int

    path: Optional[Path] = None


class FilePath(BaseModel):
    path: Path


class FileRename(BaseModel):
    path: Path
    name: str
    force: Optional[bool] = False


class FileCopyMove(BaseModel):
    path: Path
    target: Path
    force: Optional[bool] = False


from materia.models.repository import Repository
from materia.models.directory import Directory
