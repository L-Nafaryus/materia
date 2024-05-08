from uuid import UUID, uuid4 
from typing import Optional

from sqlalchemy import Column, BigInteger
from sqlalchemy.orm import mapped_column, Mapped

from src.db import Base 

class User(Base):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(primary_key = True, default = uuid4)
    login_name: Mapped[str]
    hashed_password: Mapped[str]
    name: Mapped[str]
    email: Mapped[str]
    is_admin: Mapped[bool]
    is_active: Mapped[bool]
    must_change_password: Mapped[bool]
    avatar: Mapped[str]
    created_unix = Column(BigInteger)
