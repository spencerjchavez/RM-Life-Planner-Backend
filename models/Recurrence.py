from typing import Optional, Any
from pydantic import BaseModel


class Recurrence(BaseModel):
    recurrenceId: Optional[int] = None
    userId: Optional[int] = None
    recurrenceType: Optional[int] = None
    rruleString: Optional[str] = None
    startInstant: Optional[float] = None

    eventName: Optional[str] = None
    eventType: Optional[int] = None
    eventDescription: Optional[str] = None
    eventDuration: Optional[int] = None

    todoName: Optional[str] = None
    todoTimeframe: Optional[int] = None

    goalName: Optional[str] = None
    goalHowMuch: Optional[int] = None
    goalMeasuringUnits: Optional[str] = None
    goalTimeframe: Optional[int] = None

    def get_sql_insert_query(self):
        return "INSERT INTO recurrences (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", \
            (self.userId,
             self.rruleString,
             self.startInstant,
             self.eventName,
             self.eventType,
             self.eventDescription,
             self.eventDuration,

             self.todoName,
             self.todoTimeframe,

             self.goalName,
             self.goalHowMuch,
             self.goalMeasuringUnits,
             self.todoTimeframe)