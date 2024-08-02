from uuid import UUID, uuid4
from typing import Optional, Self
import time
import re

from pydantic import BaseModel, EmailStr, ConfigDict
import pydantic
from sqlalchemy import BigInteger, Enum
from sqlalchemy.orm import mapped_column, Mapped, relationship
import sqlalchemy as sa

from materia import security
from materia.models.base import Base
from materia.models.auth.source import LoginType
from materia.models import database
from materia.models.database import SessionContext
from materia.config import Config
from loguru import logger

valid_username = re.compile(r"^[\da-zA-Z][-.\w]*$")
invalid_username = re.compile(r"[-._]{2,}|[-._]$")


class UserError(Exception):
    pass


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

    async def new(self, session: SessionContext, config: Config) -> Optional[Self]:
        # Provide checks outer

        session.add(self)
        await session.flush()
        return self

    async def remove(self, session: SessionContext):
        session.add(self)
        await session.refresh(self, attribute_names=["repository"])

        if self.repository:
            await self.repository.remove()

        await session.delete(self)
        await session.flush()

    def update_last_login(self):
        self.last_login = int(time.time())

    def is_local(self) -> bool:
        return self.login_type == LoginType.Plain

    def is_oauth2(self) -> bool:
        return self.login_type == LoginType.OAuth2

    @staticmethod
    def check_username(name: str) -> bool:
        return bool(valid_username.match(name) and not invalid_username.match(name))

    @staticmethod
    def check_password(password: str, config: Config) -> bool:
        if len(password) < config.security.password_min_length:
            return False

    @staticmethod
    async def count(session: SessionContext) -> Optional[int]:
        return await session.scalar(sa.select(sa.func.count(User.id)))

    @staticmethod
    async def by_name(
        name: str, session: SessionContext, with_lower: bool = False
    ) -> Optional[Self]:
        if with_lower:
            query = User.lower_name == name.lower()
        else:
            query = User.name == name
        return (await session.scalars(sa.select(User).where(query))).first()

    @staticmethod
    async def by_email(email: str, session: SessionContext) -> Optional[Self]:
        return (
            await session.scalars(sa.select(User).where(User.email == email))
        ).first()

    @staticmethod
    async def by_id(id: UUID, session: SessionContext) -> Optional[Self]:
        return (await session.scalars(sa.select(User).where(User.id == id))).first()

    async def edit_name(self, name: str, session: SessionContext) -> Self:
        if not User.check_username(name):
            raise UserError(f"Invalid username: {name}")

        self.name = name
        self.lower_name = name.lower()
        session.add(self)
        await session.flush()

        return self

    async def edit_password(
        self, password: str, session: SessionContext, config: Config
    ) -> Self:
        if not User.check_password(password, config):
            raise UserError("Invalid password")

        self.hashed_password = security.hash_password(
            password, algo=config.security.password_hash_algo
        )

        session.add(self)
        await session.flush()

        return self

    async def edit_email(self):
        pass

    def info(self) -> "UserInfo":
        user_info = UserInfo.model_validate(self)

        if user_info.is_email_private:
            user_info.email = None

        return user_info


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


from materia.models.repository import Repository