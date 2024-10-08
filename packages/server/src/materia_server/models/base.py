from typing import Optional, Self
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):

    def to_dict(self) -> dict:
        return {key: getattr(self, key) for key in self.__table__.columns.keys()}

    def clone(self) -> Optional[Self]:
        """Clone model.
        Included: columns and values, foreign keys
        Ignored: primary keys, relationships
        """
        # if not inspect(self).persistent:
        #    return

        cloned = self.__class__(
            **{
                key: getattr(self, key)
                for key in self.__table__.columns.keys()
                # ignore primary keys
                if key not in self.__table__.primary_key.columns.keys()
            }
        )

        return cloned
