from pydantic import BaseModel
from typing_extensions import Any


class UserAsParameter(BaseModel):
    username: str
    password: str
    email: str
    google_calendar_id: str
