from typing import Optional, Self
from uuid import UUID
from pydantic import BaseModel

from materia import db


class NewUser(BaseModel):
    login: str 
    password: str 
    email: str

class User(BaseModel):
    id: str 
    login: str 
    name: str 
    email: str 
    is_admin: bool 
    avatar: Optional[str] 


    @staticmethod
    def from_(user: db.User) -> Self:
        return User(
            id = str(user.id),
            login = user.login_name,
            name = user.name,
            email = user.email,
            is_admin = user.is_admin,
            avatar = user.avatar
        )

class RemoveUser(BaseModel):
    id: UUID

class LoginUser(BaseModel):
    email: Optional[str] = None
    login: Optional[str] = None
    password: str

