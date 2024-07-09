from time import time
from typing import Optional, Self
from pathlib import Path

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict

from materia_server.models.base import Base
from materia_server.models import database


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
    path: Mapped[str] = mapped_column(nullable=True)
    is_public: Mapped[bool] = mapped_column(default=False)
    size: Mapped[int] = mapped_column(BigInteger)

    repository: Mapped["Repository"] = relationship(back_populates="files")
    parent: Mapped["Directory"] = relationship(back_populates="files")
    link: Mapped["FileLink"] = relationship(back_populates="file")

    @staticmethod
    async def by_path(
        repository_id: int, path: Path | None, name: str, db: database.Database
    ) -> Self | None:
        async with db.session() as session:
            query_path = (
                File.path == str(path)
                if isinstance(path, Path)
                else File.path.is_(None)
            )
            return (
                await session.scalars(
                    sa.select(File).where(
                        sa.and_(
                            File.repository_id == repository_id,
                            File.name == name,
                            query_path,
                        )
                    )
                )
            ).first()

    async def remove(self, db: database.Database):
        async with db.session() as session:
            await session.delete(self)
            await session.commit()


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
    path: Optional[str]
    is_public: bool
    size: int


from materia_server.models.repository import Repository
from materia_server.models.directory import Directory
