from typing import Optional
from pydantic import BaseModel


class AuthCode(BaseModel):
    client_id: str 
    response_type: str 
    state: str 
    redirect_uri: Optional[str] 
    scope: Optional[str]

class Exchange(BaseModel):
    grant_type: str 
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None
    code: Optional[str] = None 
    refresh_token: Optional[str] = None

class AccessToken(BaseModel):
    access_token: str 
    token_type: str 
    expires_in: int 
    refresh_token: str
    scope: Optional[str]
