from time import time

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from materia.db.base import Base


class File(Base):
    __tablename__ = "file"

    id: Mapped[int] = mapped_column(BigInteger, primary_key = True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repository.id", ondelete = "CASCADE"))
    parent_id: Mapped[int] = mapped_column(ForeignKey("directory.id"), nullable = True)
    created_unix: Mapped[int] = mapped_column(BigInteger, nullable = False, default = time)
    updated_unix: Mapped[int] = mapped_column(BigInteger, nullable = False, default = time)
    name: Mapped[str]
    path: Mapped[str] = mapped_column(nullable = True)
    is_public: Mapped[bool] = mapped_column(default = False)
    size: Mapped[int] = mapped_column(BigInteger)

    repository: Mapped["Repository"] = relationship(back_populates = "files")
    parent: Mapped["Directory"] = relationship(back_populates = "files")


from materia.db.directory import Directory
from materia.db.repository import Repository
