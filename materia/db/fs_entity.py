from typing import List
from uuid import UUID, uuid4 

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from materia.db.base import Base

class FsEntity(Base):
    __tablename__ = "fs_entity"

    id = mapped_column(BigInteger, primary_key = True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("user.id", ondelete = "CASCADE"), default = uuid4)
    parent_id: Mapped[int] = mapped_column(BigInteger, nullable = False)
    created_unix: Mapped[int] = mapped_column(BigInteger, nullable = False)
    updated_unix: Mapped[int] = mapped_column(BigInteger, nullable = False)
    name: Mapped[str]
    is_private: Mapped[bool]
    is_root: Mapped[bool]
    is_file: Mapped[bool]

    children: Mapped[List["FsEntity"]] = relationship(back_populates = "parent")
    parent: Mapped["FsEntity"] = relationship(back_populates = "children")
