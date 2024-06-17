from time import time
from typing import List
from uuid import UUID, uuid4 

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from materia_server.models.base import Base


class Repository(Base):
    __tablename__ = "repository"

    id: Mapped[int] = mapped_column(BigInteger, primary_key = True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"))
    capacity: Mapped[int] = mapped_column(BigInteger, nullable = False)

    user: Mapped["User"] = relationship(back_populates = "repository")
    directories: Mapped[List["Directory"]] = relationship(back_populates = "repository")
    files: Mapped[List["File"]] = relationship(back_populates = "repository")


from materia_server.models.user.user import User
from materia_server.models.directory.directory import Directory
from materia_server.models.file.file import File
