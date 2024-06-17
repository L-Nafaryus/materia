from time import time
from typing import List, Optional, Self, Union
from uuid import UUID, uuid4 

import bcrypt
import httpx
from sqlalchemy import BigInteger, ExceptionContext, ForeignKey, JSON, and_, delete, select, update
from sqlalchemy.orm import mapped_column, Mapped, relationship
from pydantic import BaseModel, HttpUrl

from materia_server.models.base import Base
from materia_server.models.database import Database, Cache
from materia_server import security
from materia_server.models import user

class OAuth2Application(Base):
    __tablename__ = "oauth2_application"

    id: Mapped[int] = mapped_column(BigInteger, primary_key = True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id", ondelete = "CASCADE"))
    name: Mapped[str]
    client_id: Mapped[UUID] = mapped_column(default = uuid4)
    hashed_client_secret: Mapped[str]
    redirect_uris: Mapped[List[str]] = mapped_column(JSON)
    confidential_client: Mapped[bool] = mapped_column(default = True)
    created: Mapped[int] = mapped_column(BigInteger, default = time)
    updated: Mapped[int] = mapped_column(BigInteger, default = time)

    #user: Mapped["user.User"] = relationship(back_populates = "oauth2_applications")
    grants: Mapped[List["OAuth2Grant"]] = relationship(back_populates = "application")

    def contains_redirect_uri(self, uri: HttpUrl) -> bool:
        if not self.confidential_client:
            if uri.scheme == "http" and uri.host in ["127.0.0.1", "[::1]"]:
                return uri in self.redirect_uris

        else:
            if uri.scheme == "https" and uri.port == 443:
                return uri in self.redirect_uris

        return False

    async def generate_client_secret(self, db: Database) -> str:
        client_secret = security.generate_key() 
        hashed_secret = bcrypt.hashpw(client_secret, bcrypt.gensalt())

        self.hashed_client_secret = str(hashed_secret)
        
        async with db.session() as session:
            session.add(self)
            await session.commit() 

        return str(client_secret)

    def validate_client_secret(self, secret: bytes) -> bool:
        return bcrypt.checkpw(secret, self.hashed_client_secret.encode())

    @staticmethod
    async def update(db: Database, app: "OAuth2Application"):
        async with db.session() as session:
            session.add(app)
            await session.commit()

    @staticmethod
    async def delete(db: Database, id: int, user_id: int):
        async with db.session() as session:
            if not (application := (await session.scalars(
                select(OAuth2Application)
                .where(and_(OAuth2Application.id == id, OAuth2Application.user_id == user_id))
            )).first()):
                raise Exception("OAuth2Application not found")

            #await session.refresh(application, attribute_names = [ "grants" ])
            await session.delete(application)

    @staticmethod
    async def by_client_id(client_id: str, db: Database) -> Union[Self, None]:
        async with db.session() as session:
            return await session.scalar(select(OAuth2Application).where(OAuth2Application.client_id == client_id))

    async def grant_by_user_id(self, user_id: UUID, db: Database) -> Union["OAuth2Grant", None]:
        async with db.session() as session:
            return (await session.scalars(select(OAuth2Grant).where(and_(OAuth2Grant.application_id == self.id, OAuth2Grant.user_id == user_id)))).first()


class OAuth2AuthorizationCode(BaseModel):
    grant: "OAuth2Grant"
    code: str 
    redirect_uri: HttpUrl
    created: int 
    lifetime: int

    def generate_redirect_uri(self, state: Optional[str] = None) -> httpx.URL:
        redirect = httpx.URL(str(self.redirect_uri))

        if state:
            redirect = redirect.copy_add_param("state", state)

        redirect = redirect.copy_add_param("code", self.code)

        return redirect


class OAuth2Grant(Base):
    __tablename__ = "oauth2_grant"

    id: Mapped[int] = mapped_column(BigInteger, primary_key = True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id", ondelete = "CASCADE"))
    application_id: Mapped[int] = mapped_column(ForeignKey("oauth2_application.id", ondelete = "CASCADE"))
    scope: Mapped[str]
    created: Mapped[int] = mapped_column(default = time)
    updated: Mapped[int] = mapped_column(default = time)

    application: Mapped[OAuth2Application] = relationship(back_populates = "grants")

    async def generate_authorization_code(self, redirect_uri: HttpUrl, cache: Cache) -> OAuth2AuthorizationCode:
        code = OAuth2AuthorizationCode(
            grant = self,
            redirect_uri = redirect_uri,
            code = security.generate_key().decode(),
            created = int(time()), 
            lifetime = 3000
        )
        
        async with cache.client() as client:
            client.set("oauth2_authorization_code_{}".format(code.created), code.code, ex = code.lifetime)

        return code 

    def scope_contains(self, scope: str) -> bool:
        return scope in self.scope.split(" ")



