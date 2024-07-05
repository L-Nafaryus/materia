from uuid import UUID, uuid4
from typing import Optional
import time
import re

from pydantic import BaseModel, EmailStr, ConfigDict
import pydantic
from sqlalchemy import BigInteger, Enum
from sqlalchemy.orm import mapped_column, Mapped, relationship
import sqlalchemy as sa

from materia_server.models.base import Base
from materia_server.models.auth.source import LoginType
from materia_server.models import database
from loguru import logger

valid_username = re.compile(r"^[\da-zA-Z][-.\w]*$")
invalid_username = re.compile(r"[-._]{2,}|[-._]$")


class User(Base):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(unique=True)
    lower_name: Mapped[str] = mapped_column(unique=True)
    full_name: Mapped[Optional[str]]
    email: Mapped[str]
    is_email_private: Mapped[bool] = mapped_column(default=True)
    hashed_password: Mapped[str]
    must_change_password: Mapped[bool] = mapped_column(default=False)

    login_type: Mapped["LoginType"]

    created: Mapped[int] = mapped_column(BigInteger, default=time.time)
    updated: Mapped[int] = mapped_column(BigInteger, default=time.time)
    last_login: Mapped[int] = mapped_column(BigInteger, nullable=True)

    is_active: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)

    avatar: Mapped[Optional[str]]

    repository: Mapped["Repository"] = relationship(back_populates="user")

    def update_last_login(self):
        self.last_login = int(time.time())

    def is_local(self) -> bool:
        return self.login_type == LoginType.Plain

    def is_oauth2(self) -> bool:
        return self.login_type == LoginType.OAuth2

    @staticmethod
    def is_valid_username(name: str) -> bool:
        return bool(valid_username.match(name) and not invalid_username.match(name))

    @staticmethod
    async def count(db: database.Database):
        async with db.session() as session:
            return await session.scalar(sa.select(sa.func.count(User.id)))

    @staticmethod
    async def by_name(name: str, db: database.Database):
        async with db.session() as session:
            return (
                await session.scalars(sa.select(User).where(User.name == name))
            ).first()

    @staticmethod
    async def by_email(email: str, db: database.Database):
        async with db.session() as session:
            return (
                await session.scalars(sa.select(User).where(User.email == email))
            ).first()

    @staticmethod
    async def by_id(id: UUID, db: database.Database):
        async with db.session() as session:
            return (await session.scalars(sa.select(User).where(User.id == id))).first()

    async def remove(self, db: database.Database):
        async with db.session() as session:
            await session.execute(sa.delete(User).where(User.id == self.id))
            await session.commit()


class UserCredentials(BaseModel):
    name: str
    password: str
    email: Optional[EmailStr]


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    lower_name: str
    full_name: Optional[str]
    email: Optional[str]
    is_email_private: bool
    must_change_password: bool

    login_type: "LoginType"

    created: int
    updated: int
    last_login: Optional[int]

    is_active: bool
    is_admin: bool

    avatar: Optional[str]


from materia_server.models.repository import Repository
