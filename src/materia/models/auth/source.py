

import enum
from time import time

from sqlalchemy import BigInteger, Enum
from sqlalchemy.orm import Mapped, mapped_column

from materia.models.base import Base


class LoginType(enum.Enum):
    Plain = enum.auto()
    OAuth2 = enum.auto()
    Smtp = enum.auto()


class LoginSource(Base):
    __tablename__ = "login_source"

    id: Mapped[int] = mapped_column(BigInteger, primary_key = True)
    type: Mapped[LoginType]
    created: Mapped[int] = mapped_column(default = time)
    updated: Mapped[int] = mapped_column(default = time)

    def is_plain(self) -> bool:
        return self.type == LoginType.Plain 

    def is_oauth2(self) -> bool:
        return self.type == LoginType.OAuth2

    def is_smtp(self) -> bool:
        return self.type == LoginType.Smtp
