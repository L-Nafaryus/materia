from fastapi import Request

from materia_server.config import Config
from materia_server.models.database import Database, Cache
from materia_server._logging import Logger


class Context:
    def __init__(self, request: Request):
        self.config = request.state.config
        self.database = request.state.database 
        #self.cache = request.state.cache 
        self.logger = request.state.logger


