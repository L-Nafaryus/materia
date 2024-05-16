from uuid import UUID, uuid4 
from typing import Optional
import time

from sqlalchemy import BigInteger
from sqlalchemy.orm import mapped_column, Mapped, relationship

from materia.db.base import Base

class User(Base):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(primary_key = True, default = uuid4)
    login_name: Mapped[str]
    hashed_password: Mapped[str]
    name: Mapped[str]
    email: Mapped[str]
    is_admin: Mapped[bool] = mapped_column(default = False)
    is_active: Mapped[bool] = mapped_column(default = False)
    must_change_password: Mapped[bool] = mapped_column(default = False)
    avatar: Mapped[Optional[str]]
    created_unix: Mapped[int] = mapped_column(BigInteger, default = time.time)

    repository: Mapped["Repository"] = relationship(back_populates = "owner")


from materia.db.repository import Repository
