from time import time
from typing import List, Optional, Self
from pathlib import Path
import shutil
import aiofiles

from sqlalchemy import BigInteger, ForeignKey, inspect
from sqlalchemy.orm import mapped_column, Mapped, relationship
import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict

from materia.models.base import Base
from materia.models import database
from materia.models.database import SessionContext
from materia.config import Config


class DirectoryError(Exception):
    pass


class Directory(Base):
    __tablename__ = "directory"

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

    repository: Mapped["Repository"] = relationship(back_populates="directories")
    directories: Mapped[List["Directory"]] = relationship(back_populates="parent")
    parent: Mapped["Directory"] = relationship(
        back_populates="directories", remote_side=[id]
    )
    files: Mapped[List["File"]] = relationship(back_populates="parent")
    link: Mapped["DirectoryLink"] = relationship(back_populates="directory")

    async def new(self, session: SessionContext, config: Config) -> Optional[Self]:
        session.add(self)
        await session.flush()
        await session.refresh(self, attribute_names=["repository"])

        relative_path = await self.relative_path(session)
        directory_path = await self.path(session, config)

        try:
            directory_path.mkdir()
        except OSError as e:
            raise DirectoryError(
                f"Failed to create directory at /{relative_path}:",
                *e.args,
            )

        return self

    async def remove(self, session: SessionContext, config: Config):
        session.add(self)
        await session.refresh(self, attribute_names=["directories", "files"])

        if self.directories:
            for directory in self.directories:
                directory.remove(session, config)

        if self.files:
            for file in self.files:
                file.remove(session, config)

        relative_path = await self.relative_path(session)
        directory_path = await self.path(session, config)

        try:
            shutil.rmtree(str(directory_path))
        except OSError as e:
            raise DirectoryError(
                f"Failed to remove directory at /{relative_path}:", *e.args
            )

        await session.delete(self)
        await session.flush()

    async def relative_path(self, session: SessionContext) -> Optional[Path]:
        """Get relative path of the current directory"""
        if inspect(self).was_deleted:
            return None

        parts = []
        current_directory = self

        async with session.begin_nested():
            while True:
                parts.append(current_directory.name)

                session.add(current_directory)
                await session.refresh(current_directory, attribute_names=["parent"])

                if current_directory.parent is None:
                    break

                current_directory = current_directory.parent

        return Path().joinpath(*reversed(parts))

    async def path(self, session: SessionContext, config: Config) -> Optional[Path]:
        if inspect(self).was_deleted:
            return None

        repository_path = await self.repository.path(session, config)
        relative_path = await self.relative_path(session)

        return repository_path.joinpath(relative_path)

    def is_root(self) -> bool:
        return self.parent_id is None

    @staticmethod
    async def by_path(
        repository: "Repository", path: Path, session: SessionContext, config: Config
    ) -> Optional[Self]:
        if path == Path():
            raise DirectoryError("Cannot find directory by empty path")

        current_directory: Optional[Directory] = None

        for part in path.parts:
            current_directory = (
                await session.scalars(
                    sa.select(Directory).where(
                        sa.and_(
                            Directory.repository_id == repository.id,
                            Directory.name == part,
                            (
                                Directory.parent_id == current_directory.id
                                if current_directory
                                else Directory.parent_id.is_(None)
                            ),
                        )
                    )
                )
            ).first()

            if not current_directory:
                return None

        return current_directory

    async def copy(
        self, directory: Optional["Directory"], session: SessionContext, config: Config
    ) -> Self:
        pass

    async def move(
        self, directory: Optional["Directory"], session: SessionContext, config: Config
    ) -> Self:
        pass

    async def rename(self, name: str, session: SessionContext, config: Config) -> Self:
        session.add(self)

        directory_path = await self.path(session, config)
        relative_path = await self.relative_path(session)
        new_path = directory_path.with_name(name)
        identity = 1

        while True:
            if new_path == directory_path:
                break
            if not new_path.exists():
                break

            new_path = directory_path.with_name(f"{name}.{str(identity)}")
            identity += 1

        try:
            await aiofiles.os.rename(directory_path, new_path)
        except OSError as e:
            raise DirectoryError(
                f"Failed to rename directory at /{relative_path}", *e.args
            )

        self.name = new_path.name
        await session.flush()
        return self

    async def info(self) -> "DirectoryInfo":
        return DirectoryInfo.model_validate(self)


class DirectoryLink(Base):
    __tablename__ = "directory_link"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    directory_id: Mapped[int] = mapped_column(
        ForeignKey("directory.id", ondelete="CASCADE")
    )
    created: Mapped[int] = mapped_column(BigInteger, default=time)
    url: Mapped[str]

    directory: Mapped["Directory"] = relationship(back_populates="link")


class DirectoryInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_id: int
    parent_id: Optional[int]
    created: int
    updated: int
    name: str
    path: Optional[str]
    is_public: bool

    used: Optional[int] = None


from materia.models.repository import Repository
from materia.models.file import File
