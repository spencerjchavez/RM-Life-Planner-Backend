from typing import Optional

from pydantic import BaseModel
from typing_extensions import Any


class User(BaseModel):
    username: Optional[str]
    password: Optional[str]
    userId: Optional[str]
    email: Optional[str]
    googleCalendarId: Optional[str]
    dateJoined: Optional[int]
