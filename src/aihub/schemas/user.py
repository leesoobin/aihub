from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    name: str
    email: str
    access_token: str
    refresh_token: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    okta_id: str
    access_date: datetime

    class Config:
        from_attributes = True 