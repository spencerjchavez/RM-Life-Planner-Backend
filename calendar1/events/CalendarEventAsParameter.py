# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

from pydantic import BaseModel
from pydantic.config import Optional
from typing_extensions import Any


class CalendarEventAsParameter(BaseModel):
    eventId: Optional[int]
    name: Optional[str]
    description: Optional[str]
    eventType: Optional[int]
    userId: Optional[int]

    startInstant: Optional[float]
    startDay: Optional[float]  # client does not pass this
    endInstant: Optional[float]
    endDay: Optional[float]  # client does not pass this
    duration: Optional[float]  # client does not pass this
    recurrenceId: Optional[int]

    reminder1: Optional[int]  # the instant at which to remind the user of the event
    reminder2: Optional[int]
    reminder3: Optional[int]

    linkedGoalId: Optional[int]
    linkedPlanId: Optional[int]
    linkedActionId: Optional[int]
