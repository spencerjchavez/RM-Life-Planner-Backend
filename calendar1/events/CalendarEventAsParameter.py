from pydantic import BaseModel
from typing_extensions import Any


class CalendarEventAsParameter(BaseModel):
    name: str
    description: str
    eventId: int
    relatedGoals: str
    startInstant: int
    startDay: int
    duration: int
    endInstant: int
    rruleString: str
    recurrenceId: int
    isInPast: bool
    happened: bool
    report: str
    eventType: int