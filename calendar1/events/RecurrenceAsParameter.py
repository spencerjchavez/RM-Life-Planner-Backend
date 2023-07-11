from pydantic import BaseModel
from pydantic.config import Optional

class RecurrenceAsParameter(BaseModel):
    recurrenceId: Optional[int]
    userId: Optional[int]
    rruleString: Optional[str]
    recurrenceStartInstant: Optional[float]
    recurrenceEndInstant: Optional[float]
    monthyearsBuffered: Optional[bytes]
    recurrenceType: Optional[int]

    todoName: Optional[str]
    todoTimeframe: Optional[int]

    eventType: Optional[int]
    eventName: Optional[str]
    eventDescription: Optional[str]
    eventDuration: Optional[int]
