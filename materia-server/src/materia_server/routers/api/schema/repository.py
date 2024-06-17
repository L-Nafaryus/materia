from pydantic import BaseModel


class RepositoryInfo(BaseModel):
    capacity: int 
    used: int 
