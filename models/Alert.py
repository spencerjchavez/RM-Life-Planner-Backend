from typing import Optional

from pydantic import BaseModel


class Alert(BaseModel):
    time: Optional[float]
    userId: Optional[int]
    eventId: Optional[int]
