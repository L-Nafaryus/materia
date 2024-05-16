from fastapi import Request


class DatabaseState:
    def __init__(self, request: Request):
        self.connection = request.app.state.database.connection 
        self.session = request.app.state.database.session

class ConfigState:
    def __init__(self, request: Request):
        self.jwt = request.app.state.config.jwt

