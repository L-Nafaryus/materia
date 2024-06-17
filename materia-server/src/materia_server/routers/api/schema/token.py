from typing import Optional, Self
from uuid import UUID
from pydantic import BaseModel

from materia.api.token import TokenClaims


class Token(BaseModel):
    access_token: str 

