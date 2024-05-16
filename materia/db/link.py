import time
from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped

from materia.db.base import Base

class Link(Base):
    __tablename__ = "link"

    id: Mapped[int] = mapped_column(BigInteger, primary_key = True)
    directory_id: Mapped[int] = mapped_column(ForeignKey("directory.id", ondelete = "CASCADE"), nullable = True)
    file_id: Mapped[int] = mapped_column(ForeignKey("directory.id", ondelete = "CASCADE"), nullable = True)
    created_unix: Mapped[int] = mapped_column(BigInteger, nullable = False, default = time.time)
    is_file: Mapped[bool]
    url: Mapped[str]


from materia.db.directory import Directory
from materia.db.file import File
