from time import time
from typing import List, Optional, Self
from pathlib import Path

from sqlalchemy import BigInteger, ForeignKey, inspect
from sqlalchemy.orm import mapped_column, Mapped, relationship
import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict

from materia.models.base import Base
from materia.core import SessionContext, Config, FileSystem


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

        repository_path = await self.repository.real_path(session, config)
        directory_path = await self.real_path(session, config)

        new_directory = FileSystem(directory_path, repository_path)
        await new_directory.make_directory()

        return self

    async def remove(self, session: SessionContext, config: Config):
        session.add(self)
        await session.refresh(
            self, attribute_names=["repository", "directories", "files"]
        )

        if self.directories:
            for directory in self.directories:
                directory.remove(session, config)

        if self.files:
            for file in self.files:
                file.remove(session, config)

        repository_path = await self.repository.real_path(session, config)
        directory_path = await self.real_path(session, config)

        current_directory = FileSystem(directory_path, repository_path)
        await current_directory.remove()

        await session.delete(self)
        await session.flush()

    async def relative_path(self, session: SessionContext) -> Optional[Path]:
        """Get path of the directory relative repository root."""
        if inspect(self).was_deleted:
            return None

        parts = []
        current_directory = self

        while True:
            # ISSUE: accessing `parent` attribute raises greenlet_spawn has not been called; can't call await_only() here
            # parts.append(current_directory.name)
            # session.add(current_directory)
            # await session.refresh(current_directory, attribute_names=["parent"])
            # if current_directory.parent is None:
            #    break
            # current_directory = current_directory.parent

            parts.append(current_directory.name)

            if current_directory.parent_id is None:
                break

            current_directory = (
                await session.scalars(
                    sa.select(Directory).where(
                        Directory.id == current_directory.parent_id,
                    )
                )
            ).first()

        return Path().joinpath(*reversed(parts))

    async def real_path(
        self, session: SessionContext, config: Config
    ) -> Optional[Path]:
        """Get absolute path of the directory"""
        if inspect(self).was_deleted:
            return None

        repository_path = await self.repository.real_path(session, config)
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
            # from root directory to target directory
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
        self,
        target: Optional["Directory"],
        session: SessionContext,
        config: Config,
        force: bool = False,
        shallow: bool = False,
    ) -> Self:
        session.add(self)
        await session.refresh(self, attribute_names=["repository"])

        repository_path = await self.repository.real_path(session, config)
        directory_path = await self.real_path(session, config)
        target_path = (
            await target.real_path(session, config) if target else repository_path
        )

        current_directory = FileSystem(directory_path, repository_path)
        new_directory = await current_directory.copy(
            target_path, force=force, shallow=shallow
        )

        cloned = self.clone()
        cloned.name = new_directory.name()
        cloned.parent_id = target.id if target else None
        session.add(cloned)
        await session.flush()

        await session.refresh(self, attribute_names=["files", "directories"])
        for directory in self.directories:
            await directory.copy(cloned, session, config, shallow=True)
        for file in self.files:
            await file.copy(cloned, session, config, shallow=True)

        return self

    async def move(
        self,
        target: Optional["Directory"],
        session: SessionContext,
        config: Config,
        force: bool = False,
        shallow: bool = False,
    ) -> Self:
        session.add(self)
        await session.refresh(self, attribute_names=["repository"])

        repository_path = await self.repository.real_path(session, config)
        directory_path = await self.real_path(session, config)
        target_path = (
            await target.real_path(session, config) if target else repository_path
        )

        current_directory = FileSystem(directory_path, repository_path)
        moved_directory = await current_directory.move(
            target_path, force=force, shallow=shallow
        )

        self.name = moved_directory.name()
        self.parent_id = target.id if target else None
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
        directory_path = await self.real_path(session, config)

        current_directory = FileSystem(directory_path, repository_path)
        renamed_directory = await current_directory.rename(
            name, force=force, shallow=shallow
        )

        self.name = renamed_directory.name()
        await session.flush()
        return self

    async def info(self, session: SessionContext) -> "DirectoryInfo":
        session.add(self)
        await session.refresh(self, attribute_names=["files"])

        info = DirectoryInfo.model_validate(self)

        relative_path = await self.relative_path(session)

        info.path = Path("/").joinpath(relative_path) if relative_path else None
        info.used = sum([file.size for file in self.files])

        return info


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
    is_public: bool

    path: Optional[Path] = None
    used: Optional[int] = None


class DirectoryPath(BaseModel):
    path: Path


class DirectoryRename(BaseModel):
    path: Path
    name: str
    force: Optional[bool] = False


class DirectoryCopyMove(BaseModel):
    path: Path
    target: Path
    force: Optional[bool] = False


from materia.models.repository import Repository
from materia.models.file import File
