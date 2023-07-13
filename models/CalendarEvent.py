# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

from pydantic import BaseModel
from typing import Optional


class CalendarEvent(BaseModel):
    eventId: Optional[int]
    userId: Optional[int]
    name: Optional[str]
    description: Optional[str]
    eventType: Optional[int]

    startInstant: Optional[float]
    endInstant: Optional[float]
    duration: Optional[float]  # client does not pass this

    linkedGoalId: Optional[int]
    recurrenceId: Optional[int]