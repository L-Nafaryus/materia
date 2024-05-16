from os import environ
from pathlib import Path 
from typing import Self

from pydantic import BaseModel
import toml 

class Database(BaseModel):
    host: str 
    port: int 
    user: str 
    password: str 
    name: str 

class Server(BaseModel):
    address: str 
    port: int 

class Jwt(BaseModel):
    secret: str 
    expires_in: str 
    maxage: int 

class Config(BaseModel):
    database: Database 
    server: Server 
    jwt: Jwt 

    @staticmethod
    def default() -> Self:
        return Config(**{
            "database": Database(**{
                "host": "localhost",
                "port": 5432,
                "user": "materia",
                "password": "test",
                "name": "materia"
            }), 
            "server": Server(**{
                "address": "127.0.0.1",
                "port": 54601
            }), 
            "jwt": Jwt(**{
                "secret": "change_this_secret",
                "expires_in": "60m",
                "maxage": 3600
            })
        })

    def database_url(self) -> str:
        return "postgresql+asyncpg://{}:{}@{}:{}/{}".format(
            self.database.user,
            self.database.password,
            self.database.host,
            self.database.port,
            self.database.name
        )

    @staticmethod
    def open(path: Path) -> Self | None:
        try:
            data: dict = toml.load(path)
        except:
            return None
        else:
            return Config(**data)

    def write(self, path: Path):
        with open(path, "w") as file:
            toml.dump(self.model_dump(), file)

    @staticmethod
    def data_dir() -> Path:
        cwd = Path.cwd()
        if environ.get("MATERIA_DEBUG"):
            return cwd / "temp"
        else:
            return cwd


# initialize config
if not (config := Config.open(Config.data_dir().joinpath("config.toml"))):
    config = Config.default()
