from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class UserCreate(BaseModel):
    username: str
    password: str
    admin: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: int
    username: str
    admin: bool

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class PaginatedUserResponse(BaseModel):
    page: int
    total_pages: int
    users: List[UserResponse]
