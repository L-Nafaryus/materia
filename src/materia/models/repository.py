from typing import List, Self, Optional
from uuid import UUID
from pathlib import Path
import shutil

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict

from materia.models.base import Base
from materia.core import SessionContext, Config


class RepositoryError(Exception):
    pass


class Repository(Base):
    __tablename__ = "repository"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    capacity: Mapped[int] = mapped_column(BigInteger, nullable=False)

    user: Mapped["User"] = relationship(back_populates="repository")
    directories: Mapped[List["Directory"]] = relationship(back_populates="repository")
    files: Mapped[List["File"]] = relationship(back_populates="repository")

    async def new(self, session: SessionContext, config: Config) -> Optional[Self]:
        session.add(self)
        await session.flush()

        repository_path = await self.real_path(session, config)
        relative_path = repository_path.relative_to(
            config.application.working_directory
        )

        try:
            repository_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RepositoryError(
                f"Failed to create repository at /{relative_path}:",
                *e.args,
            )

        await session.flush()

        return self

    async def real_path(self, session: SessionContext, config: Config) -> Path:
        """Get absolute path of the directory."""
        session.add(self)
        await session.refresh(self, attribute_names=["user"])

        repository_path = config.application.working_directory.joinpath(
            "repository", self.user.lower_name
        )

        return repository_path

    async def remove(self, session: SessionContext, config: Config):
        session.add(self)
        await session.refresh(self, attribute_names=["directories", "files"])

        for directory in self.directories:
            if directory.is_root():
                await directory.remove(session)

        for file in self.files:
            await file.remove(session)

        repository_path = await self.real_path(session, config)

        try:
            shutil.rmtree(str(repository_path))
        except OSError as e:
            raise RepositoryError(
                f"Failed to remove repository at /{repository_path.relative_to(config.application.working_directory)}:",
                *e.args,
            )

        await session.delete(self)
        await session.flush()

    async def update(self, session: SessionContext):
        await session.execute(
            sa.update(Repository).values(self.to_dict()).where(Repository.id == self.id)
        )
        await session.flush()

    @staticmethod
    async def from_user(user: "User", session: SessionContext) -> Optional[Self]:
        session.add(user)
        await session.refresh(user, attribute_names=["repository"])
        return user.repository

    async def used(self, session: SessionContext) -> int:
        session.add(self)
        await session.refresh(self, attribute_names=["files"])

        return sum([file.size for file in self.files])

    async def remaining_capacity(self, session: SessionContext) -> int:
        used = await self.used(session)
        return self.capacity - used

    async def info(self, session: SessionContext) -> "RepositoryInfo":
        info = RepositoryInfo.model_validate(self)
        info.used = await self.used(session)

        return info


class RepositoryInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    capacity: int
    used: Optional[int] = None


class RepositoryContent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    files: list["FileInfo"]
    directories: list["DirectoryInfo"]


from materia.models.user import User
from materia.models.directory import Directory, DirectoryInfo
from materia.models.file import File, FileInfo
