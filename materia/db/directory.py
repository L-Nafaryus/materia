from time import time
from typing import List

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from materia.db.base import Base


class Directory(Base):
    __tablename__ = "directory"

    id: Mapped[int] = mapped_column(BigInteger, primary_key = True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repository.id", ondelete = "CASCADE"))
    parent_id: Mapped[int] = mapped_column(ForeignKey("directory.id"), nullable = True)
    created_unix: Mapped[int] = mapped_column(BigInteger, nullable = False, default = time)
    updated_unix: Mapped[int] = mapped_column(BigInteger, nullable = False, default = time)
    name: Mapped[str]
    path: Mapped[str] = mapped_column(nullable = True)
    is_public: Mapped[bool] = mapped_column(default = False)

    repository: Mapped["Repository"] = relationship(back_populates = "directories")
    directories: Mapped[List["Directory"]] = relationship(back_populates = "parent", remote_side = [id])
    parent: Mapped["Directory"] = relationship(back_populates = "directories")
    files: Mapped[List["File"]] = relationship(back_populates = "parent")


from materia.db.repository import Repository
from materia.db.file import File
