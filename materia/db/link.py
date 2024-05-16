import time
from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped

from materia.db.base import Base

class Link(Base):
    __tablename__ = "link"

    id: Mapped[int] = mapped_column(BigInteger, primary_key = True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("fs_entity.id", ondelete = "CASCADE"))
    created_unix: Mapped[int] = mapped_column(BigInteger, nullable = False, default = time.time)
    is_public: Mapped[bool]
