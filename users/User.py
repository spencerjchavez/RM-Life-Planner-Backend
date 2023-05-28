from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    username: Optional[str]
    hashed_password: Optional[str]
    user_id: Optional[int]
    email: Optional[str]
    date_joined: Optional[int]
    google_calendar_id: Optional[str]
    salt: Optional[str] = None


