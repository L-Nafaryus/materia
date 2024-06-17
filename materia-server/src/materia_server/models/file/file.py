from time import time

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from materia_server.models.base import Base


class File(Base):
    __tablename__ = "file"

    id: Mapped[int] = mapped_column(BigInteger, primary_key = True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repository.id", ondelete = "CASCADE"))
    parent_id: Mapped[int] = mapped_column(ForeignKey("directory.id"), nullable = True)
    created: Mapped[int] = mapped_column(BigInteger, nullable = False, default = time)
    updated: Mapped[int] = mapped_column(BigInteger, nullable = False, default = time)
    name: Mapped[str]
    path: Mapped[str] = mapped_column(nullable = True)
    is_public: Mapped[bool] = mapped_column(default = False)
    size: Mapped[int] = mapped_column(BigInteger)

    repository: Mapped["Repository"] = relationship(back_populates = "files")
    parent: Mapped["Directory"] = relationship(back_populates = "files")
    link: Mapped["FileLink"] = relationship(back_populates = "file")


class FileLink(Base):
    __tablename__ = "file_link"

    id: Mapped[int] = mapped_column(BigInteger, primary_key = True)
    file_id: Mapped[int] = mapped_column(ForeignKey("file.id", ondelete = "CASCADE"))
    created: Mapped[int] = mapped_column(BigInteger, default = time)
    url: Mapped[str]

    file: Mapped["File"] = relationship(back_populates = "link")


from materia_server.models.repository.repository import Repository
from materia_server.models.directory.directory import Directory
