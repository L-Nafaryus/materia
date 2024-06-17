from time import time
from typing import List

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from materia_server.models.base import Base


class Directory(Base):
    __tablename__ = "directory"

    id: Mapped[int] = mapped_column(BigInteger, primary_key = True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repository.id", ondelete = "CASCADE"))
    parent_id: Mapped[int] = mapped_column(ForeignKey("directory.id"), nullable = True)
    created: Mapped[int] = mapped_column(BigInteger, nullable = False, default = time)
    updated: Mapped[int] = mapped_column(BigInteger, nullable = False, default = time)
    name: Mapped[str]
    path: Mapped[str] = mapped_column(nullable = True)
    is_public: Mapped[bool] = mapped_column(default = False)

    repository: Mapped["Repository"] = relationship(back_populates = "directories")
    directories: Mapped[List["Directory"]] = relationship(back_populates = "parent", remote_side = [id])
    parent: Mapped["Directory"] = relationship(back_populates = "directories")
    files: Mapped[List["File"]] = relationship(back_populates = "parent")
    link: Mapped["DirectoryLink"] = relationship(back_populates = "directory")


class DirectoryLink(Base):
    __tablename__ = "directory_link"

    id: Mapped[int] = mapped_column(BigInteger, primary_key = True)
    directory_id: Mapped[int] = mapped_column(ForeignKey("directory.id", ondelete = "CASCADE"))
    created: Mapped[int] = mapped_column(BigInteger, default = time)
    url: Mapped[str]

    directory: Mapped["Directory"] = relationship(back_populates = "link")

from materia_server.models.repository.repository import Repository
from materia_server.models.file.file import File
