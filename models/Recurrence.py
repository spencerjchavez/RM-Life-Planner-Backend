from typing import Optional, Any
from pydantic import BaseModel
from models.SQLColumnNames import *


class Recurrence(BaseModel):
    recurrenceId: Optional[int] = None
    seriesId: Optional[int] = None
    userId: Optional[int] = None
    rruleString: Optional[str] = None
    startInstant: Optional[float] = None

    eventName: Optional[str] = None
    eventDescription: Optional[str] = None
    eventDuration: Optional[int] = None

    todoName: Optional[str] = None
    todoTimeframe: Optional[int] = None

    goalName: Optional[str] = None
    goalDesireId: Optional[int] = None
    goalHowMuch: Optional[int] = None
    goalMeasuringUnits: Optional[str] = None
    goalTimeframe: Optional[int] = None

    def get_sql_insert_query(self):
        return "INSERT INTO recurrences VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (None,
                self.userId,
                self.seriesId,
                self.rruleString,
                self.startInstant,

                self.eventName,
                self.eventDescription,
                self.eventDuration,

                self.todoName,
                self.todoTimeframe,

                self.goalName,
                self.goalDesireId,
                self.goalHowMuch,
                self.goalMeasuringUnits,
                self.goalTimeframe)
    @staticmethod
    def from_sql_res(src: dict):
        return Recurrence(
            recurrenceId=src[RECURRENCE_ID],
            userId=src[USER_ID],
            seriesId=src["series_id"],
            rruleString=src[RRULE_STRING],
            startInstant=src[START_INSTANT],

            eventName=src[RECURRENCE_EVENT_NAME],
            eventDescription=src[RECURRENCE_EVENT_DESCRIPTION],
            eventDuration=src[RECURRENCE_EVENT_DURATION],

            todoName=src[RECURRENCE_TODO_NAME],
            todoTimeframe=src[RECURRENCE_TODO_TIMEFRAME],

            goalName=src[RECURRENCE_GOAL_NAME],
            goalDesireId=src[RECURRENCE_GOAL_DESIRE_ID],
            goalHowMuch=src[RECURRENCE_GOAL_HOW_MUCH],
            goalMeasuringUnits=src[RECURRENCE_GOAL_MEASURING_UNITS],
            goalTimeframe=src[RECURRENCE_GOAL_TIMEFRAME]
        )