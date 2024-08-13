from typing import Optional
import datetime

from pydantic import BaseModel
import jwt


class TokenClaims(BaseModel):
    sub: str
    exp: int
    iat: int
    iss: Optional[str] = None


def generate_token(
    sub: str, secret: str, duration: int, iss: Optional[str] = None
) -> str:
    now = datetime.datetime.now()
    iat = now.timestamp()
    exp = (now + datetime.timedelta(seconds=duration)).timestamp()
    claims = TokenClaims(sub=sub, exp=int(exp), iat=int(iat), iss=iss)

    return jwt.encode(claims.model_dump(), secret)


def validate_token(token: str, secret: str) -> TokenClaims:
    payload = jwt.decode(token, secret, algorithms=["HS256"])

    return TokenClaims(**payload)
