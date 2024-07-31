from time import time
from typing import List, Self, Optional
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.orm.attributes import InstrumentedAttribute
import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict

from materia.models.base import Base
from materia.models import database


class Repository(Base):
    __tablename__ = "repository"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    capacity: Mapped[int] = mapped_column(BigInteger, nullable=False)

    user: Mapped["User"] = relationship(back_populates="repository")
    directories: Mapped[List["Directory"]] = relationship(back_populates="repository")
    files: Mapped[List["File"]] = relationship(back_populates="repository")

    def to_dict(self) -> dict:
        return {
            k: getattr(self, k)
            for k, v in Repository.__dict__.items()
            if isinstance(v, InstrumentedAttribute)
        }

    async def create(self, db: database.Database):
        async with db.session() as session:
            session.add(self)
            await session.commit()

    async def update(self, db: database.Database):
        async with db.session() as session:
            await session.execute(
                sa.update(Repository)
                .where(Repository.id == self.id)
                .values(self.to_dict())
            )
            await session.commit()

    @staticmethod
    async def by_user_id(user_id: UUID, db: database.Database) -> Self | None:
        async with db.session() as session:
            return (
                await session.scalars(
                    sa.select(Repository).where(Repository.user_id == user_id)
                )
            ).first()

    async def remove(self, db: database.Database):
        async with db.session() as session:
            await session.delete(self)
            await session.commit()


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
