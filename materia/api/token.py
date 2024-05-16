from typing import Self
import jwt 
from pydantic import BaseModel
import time 
import datetime 


class TokenClaims(BaseModel):
    sub: str 
    exp: int 
    iat: int 

    @staticmethod
    def create(sub: str, secret: str, duration: int) -> str:
        now = datetime.datetime.now()
        iat = now.timestamp()
        exp = (now + datetime.timedelta(seconds = duration)).timestamp()
        claims = TokenClaims(sub = sub, exp = int(exp), iat = int(iat))

        return jwt.encode(claims.model_dump(), secret)

    @staticmethod
    def verify(token: str, secret: str) -> Self:
        data = jwt.decode(token, secret, algorithms = ["HS256"])
        
        return TokenClaims(**data)

