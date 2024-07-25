from os import environ
from pathlib import Path
import sys
from typing import Any, Literal, Optional, Self, Union

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    model_validator,
    TypeAdapter,
    PostgresDsn,
    NameEmail,
)
from pydantic_settings import BaseSettings
from pydantic.networks import IPvAnyAddress
import toml


class Application(BaseModel):
    user: str = "materia"
    group: str = "materia"
    mode: Literal["production", "development"] = "production"
    working_directory: Optional[Path] = Path.cwd()


class Log(BaseModel):
    mode: Literal["console", "file", "all"] = "console"
    level: Literal["info", "warning", "error", "critical", "debug", "trace"] = "info"
    console_format: str = (
        "<level>{level: <8}</level> <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> - {message}"
    )
    file_format: str = (
        "<level>{level: <8}</level>: <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> - {message}"
    )
    file: Optional[Path] = None
    file_rotation: str = "3 days"
    file_retention: str = "1 week"


class Server(BaseModel):
    scheme: Literal["http", "https"] = "http"
    address: IPvAnyAddress = Field(default="127.0.0.1")
    port: int = 54601
    domain: str = "localhost"


class Database(BaseModel):
    backend: Literal["postgresql"] = "postgresql"
    scheme: Literal["postgresql+asyncpg"] = "postgresql+asyncpg"
    address: IPvAnyAddress = Field(default="127.0.0.1")
    port: int = 5432
    name: Optional[str] = "materia"
    user: str = "materia"
    password: Optional[Union[str, Path]] = None
    # ssl: bool = False

    def url(self) -> str:
        if self.backend in ["postgresql"]:
            return (
                "{}://{}:{}@{}:{}".format(
                    self.scheme, self.user, self.password, self.address, self.port
                )
                + f"/{self.name}"
                if self.name
                else ""
            )
        else:
            raise NotImplementedError()


class Cache(BaseModel):
    backend: Literal["redis"] = "redis"  # add: memory
    # gc_interval: Optional[int] = 60   # for: memory
    scheme: Literal["redis", "rediss"] = "redis"
    address: Optional[IPvAnyAddress] = Field(default="127.0.0.1")
    port: Optional[int] = 6379
    user: Optional[str] = None
    password: Optional[Union[str, Path]] = None
    database: Optional[int] = 0  # for: redis

    def url(self) -> str:
        if self.backend in ["redis"]:
            if self.user and self.password:
                return "{}://{}:{}@{}:{}/{}".format(
                    self.scheme,
                    self.user,
                    self.password,
                    self.address,
                    self.port,
                    self.database,
                )
            else:
                return "{}://{}:{}/{}".format(
                    self.scheme, self.address, self.port, self.database
                )
        else:
            raise NotImplemented()


class Security(BaseModel):
    secret_key: Optional[Union[str, Path]] = None
    password_min_length: int = 8
    password_hash_algo: Literal["bcrypt"] = "bcrypt"
    cookie_http_only: bool = True
    cookie_access_token_name: str = "materia_at"
    cookie_refresh_token_name: str = "materia_rt"


class OAuth2(BaseModel):
    enabled: bool = True
    jwt_signing_algo: Literal["HS256"] = "HS256"
    # check if signing algo need a key or generate it | HS256, HS384, HS512, RS256, RS384, RS512, ES256, ES384, ES512, EdDSA
    jwt_signing_key: Optional[Union[str, Path]] = None
    jwt_secret: Optional[Union[str, Path]] = (
        None  # only for HS256, HS384, HS512 | generate
    )
    access_token_lifetime: int = 3600
    refresh_token_lifetime: int = 730 * 60
    refresh_token_validation: bool = False

    # @model_validator(mode = "after")
    # def check(self) -> Self:
    #    if self.jwt_signing_algo in ["HS256", "HS384", "HS512"]:
    #        assert self.jwt_secret is not None, "JWT secret must be set for HS256, HS384, HS512 algorithms"
    #    else:
    #        assert self.jwt_signing_key is not None, "JWT signing key must be set"
    #
    #    return self


class Mailer(BaseModel):
    enabled: bool = False
    scheme: Optional[Literal["smtp", "smtps", "smtp+starttls"]] = None
    address: Optional[IPvAnyAddress] = None
    port: Optional[int] = None
    helo: bool = True

    cert_file: Optional[Path] = None
    key_file: Optional[Path] = None

    from_: Optional[NameEmail] = None
    user: Optional[str] = None
    password: Optional[str] = None
    plain_text: bool = False


class Cron(BaseModel):
    pass


class Repository(BaseModel):
    capacity: int = 41943040


class Config(BaseSettings, env_prefix="materia_", env_nested_delimiter="_"):
    application: Application = Application()
    log: Log = Log()
    server: Server = Server()
    database: Database = Database()
    cache: Cache = Cache()
    security: Security = Security()
    oauth2: OAuth2 = OAuth2()
    mailer: Mailer = Mailer()
    cron: Cron = Cron()
    repository: Repository = Repository()

    @staticmethod
    def open(path: Path) -> Self | None:
        try:
            data: dict = toml.load(path)
        except Exception as e:
            raise e
            # return None
        else:
            return Config(**data)

    def write(self, path: Path):
        dump = self.model_dump()

        # TODO: make normal filter or check model_dump abilities
        for key_first in dump.keys():
            for key_second in dump[key_first].keys():
                if isinstance(dump[key_first][key_second], Path):
                    dump[key_first][key_second] = str(dump[key_first][key_second])

        with open(path, "w") as file:
            toml.dump(dump, file)

    @staticmethod
    def data_dir() -> Path:
        cwd = Path.cwd()
        if environ.get("MATERIA_DEBUG"):
            return cwd / "temp"
        else:
            return cwd
