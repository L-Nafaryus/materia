from pydantic import BaseModel


class DirectoryInfo(BaseModel):
    id: int
    created_at: int
    updated_at: int
    name: str
    path: str
    is_public: bool
    used: int 
