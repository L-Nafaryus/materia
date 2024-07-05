from time import time
from typing import List, Optional, Self
from pathlib import Path

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict

from materia_server.models.base import Base
from materia_server.models import database


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
    path: Mapped[str] = mapped_column(nullable=True)
    is_public: Mapped[bool] = mapped_column(default=False)

    repository: Mapped["Repository"] = relationship(back_populates="directories")
    directories: Mapped[List["Directory"]] = relationship(
        back_populates="parent", remote_side=[id]
    )
    parent: Mapped["Directory"] = relationship(back_populates="directories")
    files: Mapped[List["File"]] = relationship(back_populates="parent")
    link: Mapped["DirectoryLink"] = relationship(back_populates="directory")

    @staticmethod
    async def by_path(
        repository_id: int, path: Path | None, name: str, db: database.Database
    ) -> Self | None:
        async with db.session() as session:
            query_path = (
                Directory.path == str(path)
                if isinstance(path, Path)
                else Directory.path.is_(None)
            )
            return (
                await session.scalars(
                    sa.select(Directory).where(
                        sa.and_(
                            Directory.repository_id == repository_id,
                            Directory.name == name,
                            query_path,
                        )
                    )
                )
            ).first()

    async def remove(self, db: database.Database):
        async with db.session() as session:
            await session.execute(sa.delete(Directory).where(Directory.id == self.id))
            await session.commit()


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


from materia_server.models.repository import Repository
from materia_server.models.file import File
