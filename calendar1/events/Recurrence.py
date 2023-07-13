from pydantic import BaseModel
from pydantic.config import Optional

class Recurrence(BaseModel):
    recurrenceId: Optional[int]
    userId: Optional[int]
    recurrenceType: Optional[int]
    rruleString: Optional[str]
    startInstant: Optional[float]

    recurrenceType: Optional[int]

    todoName: Optional[str]
    todoTimeframe: Optional[int]

    eventType: Optional[int]
    eventName: Optional[str]
    eventDescription: Optional[str]
    eventDuration: Optional[int]

    goalName: Optional[str]
    goalHowMuch: Optional[int]
    goalMeasuringUnits: Optional[str]
    goalTimeframe: Optional[int]
