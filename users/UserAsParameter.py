from typing import Optional

from pydantic import BaseModel
from typing_extensions import Any


class UserAsParameter(BaseModel):
    username: Optional[str]
    password: Optional[str]
    email: Optional[str]
    google_calendar_id: Optional[str]
