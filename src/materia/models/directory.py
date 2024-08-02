from time import time
from typing import List, Optional, Self
from pathlib import Path
import shutil

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict

from materia.models.base import Base
from materia.models import database
from materia.models.database import SessionContext


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
    directories: Mapped[List["Directory"]] = relationship(
        back_populates="parent", remote_side=[id]
    )
    parent: Mapped["Directory"] = relationship(back_populates="directories")
    files: Mapped[List["File"]] = relationship(back_populates="parent")
    link: Mapped["DirectoryLink"] = relationship(back_populates="directory")

    async def new(
        self,
        session: SessionContext,
        path: Optional[Path] = None,
        with_parents: bool = False,
    ) -> Optional[Self]:
        session.add(self)
        await session.flush()
        await session.refresh(self, attribute_names=["repository", "parent"])

        repository_path: Path = await self.repository.path(session)
        current_path: Path = repository_path
        current_directory: Optional[Directory] = None

        for part in path.parts:
            current_path /= part
            relative_path = current_path.relative_to(repository_path)

            if current_path.exists() and current_path.is_dir():
                # Find record
                current_directory = await Directory.find(
                    self.repository, self.parent, self.name, session
                )

                if not current_directory:
                    # TODO: recreate record
                    raise DirectoryError(
                        f"No directory was found in the records: {relative_path}"
                    )

                current_directory.updated = time()
                await session.flush()

                continue

            if not with_parents:
                raise DirectoryError(f"Directory not exists at /{relative_path}")

            # Create an ancestor directory from scratch
            current_directory = await Directory(
                repository_id=self.repository.id,
                parent_id=current_directory.id if current_directory else None,
                name=part,
            ).new(
                session,
                path=relative_path,
                with_parents=False,
            )

            try:
                current_path.mkdir()
            except OSError as e:
                raise DirectoryError(
                    f"Failed to create directory at /{relative_path}:", *e.args
                )

        # Create directory
        current_path /= self.name
        relative_path = current_path.relative_to(repository_path)

        try:
            current_path.mkdir()
        except OSError as e:
            raise DirectoryError(
                f"Failed to create directory at /{relative_path}:", *e.args
            )

        # Update information
        self.parent = current_directory

        await session.commit()

        return self

    async def remove(self, session: SessionContext):
        session.add(self)

        current_path: Path = self.repository.path(session) / self.path(session)

        try:
            shutil.tmtree(str(current_path))
        except OSError as e:
            raise DirectoryError("Failed to remove directory:", *e.args)

        await session.refresh(self, attribute_names=["parent"])
        current_directory: Directory = self.parent

        while current_directory:
            current_directory.updated = time()
            session.add(current_directory)
            await session.refresh(self, attribute_names=["parent"])
            current_directory = current_directory.parent

        await session.delete(self)
        await session.commit()

    async def is_root(self) -> bool:
        return self.parent_id is None

    @staticmethod
    async def find(
        repository: "Repository",
        directory: "Directory",
        name: str,
        session: SessionContext,
    ) -> Optional[Self]:
        return (
            await session.scalars(
                sa.select(Directory).where(
                    sa.and_(
                        Directory.repository_id == repository.id,
                        Directory.name == name,
                        Directory.parent_id == directory.parent_id,
                    )
                )
            )
        ).first()

    async def find_nested(self, session: SessionContext):
        pass

    async def find_by_descend(
        self, path: Path | str, db: database.Database, need_create: bool = False
    ) -> Optional[Self]:
        """Find a nested directory from current"""
        repository_id = self.repository_id
        path = Path(path)
        current_directory = self

        async with db.session() as session:
            for part in path.parts:
                directory = (
                    await session.scalars(
                        sa.select(Directory).where(
                            sa.and_(
                                Directory.repository_id == repository_id,
                                Directory.name == part,
                                Directory.parent_id == current_directory.id,
                            )
                        )
                    )
                ).first()

                if directory is None:
                    if not need_create:
                        return None

                    directory = Directory(
                        repository_id=repository_id,
                        parent_id=current_directory.id,
                        name=part,
                    )
                    session.add(directory)
                    await session.flush()

                current_directory = directory

            if need_create:
                await session.commit()

        return current_directory

    @staticmethod
    async def find_by_path(
        repository_id: int, path: Path | str, db: database.Database
    ) -> Optional[Self]:
        """Find a directory by given absolute path"""
        path = Path(path)
        assert path == Path(), "The path cannot be empty"

        root = await Directory.find_by_descend(repository_id, path.parts[0], db)
        return root.descend(Path().joinpath(*path.parts[1:]), db)

    async def path(self, session: SessionContext) -> Optional[Path]:
        """Get relative path of the current directory"""
        parts = []
        current_directory = self

        while True:
            parts.append(current_directory.name)
            session.add(current_directory)
            await session.refresh(current_directory, attribute_names=["parent"])

            if current_directory.parent is None:
                break

            current_directory = current_directory.parent

        return Path().joinpath(*reversed(parts))

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
