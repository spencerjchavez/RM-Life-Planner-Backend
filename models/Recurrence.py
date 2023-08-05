from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel

from models.Goal import Goal
from models.ToDo import ToDo
from models.CalendarEvent import CalendarEvent
from models.SQLColumnNames import *
from datetime import datetime, timedelta
from dateutil import relativedelta


class Recurrence(BaseModel):

    class Timeframe(Enum):
        INDEFINITE = 0
        DAY = 1
        WEEK = 2
        MONTH = 3
        YEAR = 4

    recurrenceId: Optional[int] = None
    userId: Optional[int] = None
    rruleString: Optional[str] = None
    startInstant: Optional[float] = None

    eventName: Optional[str] = None
    eventDescription: Optional[str] = None
    eventDuration: Optional[int] = None

    todoName: Optional[str] = None
    todoTimeframe: Optional[Timeframe] = None

    goalName: Optional[str] = None
    goalDesireId: Optional[int] = None
    goalHowMuch: Optional[int] = None
    goalMeasuringUnits: Optional[str] = None
    goalTimeframe: Optional[Timeframe] = None

    def get_sql_insert_query(self):
        return "INSERT INTO recurrences VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (None,
                self.userId,
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

    def generate_instance_objects(self, dt: datetime):
        # REDO THIS
        start_dt = datetime.fromtimestamp(self.startInstant)
        hours = start_dt.hour
        minutes = start_dt.minute
        seconds = start_dt.second
        event_start_offset = (hours * 60 + minutes) * 60 + seconds
        day_start = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        todo_end_instant: datetime
        if self.todoTimeframe == Recurrence.Timeframe.YEAR:
            todo_end_instant = day_start + relativedelta.relativedelta(years=1)
        elif self.todoTimeframe == Recurrence.Timeframe.MONTH:
            todo_end_instant = day_start + relativedelta.relativedelta(months=1)
        elif self.todoTimeframe == Recurrence.Timeframe.WEEK:
            todo_end_instant = day_start + relativedelta.relativedelta(weeks=1)
        else:  # == Timeframe.DAY
            todo_end_instant = day_start + relativedelta.relativedelta(days=1)

        goal = None
        todo = None
        event = None
        if self.goalName is not None:
            goal = Goal()
            goal.name = self.goalName
            goal.userId = self.userId
            goal.desireId = self.goalDesireId
            goal.howMuch = self.goalHowMuch
            goal.measuringUnits = self.goalMeasuringUnits
            goal.timeframe = self.goalTimeframe
            goal.startInstant = day_start.timestamp()
            goal.endInstant = todo_end_instant.timestamp()
            goal.recurrenceId = self.recurrenceId
            goal.recurrenceDay = day_start.timestamp()

        if self.todoName is not None:
            todo = ToDo()
            todo.name = self.todoName
            todo.recurrenceId = self.recurrenceId
            todo.userId = self.userId
            todo.startInstant = day_start.timestamp()
            todo.timeframe = self.todoTimeframe
            todo.endInstant = todo_end_instant.timestamp()
            todo.recurrenceDay = day_start.timestamp()


        if self.eventName is not None:
            event = CalendarEvent()
            event.name = self.eventName
            event.description = self.eventDescription
            event.startInstant = dt.timestamp() + event_start_offset
            event.endInstant = event.startInstant + self.eventDuration
            event.duration = self.eventDuration
            event.userId = self.userId
            event.recurrenceId = self.recurrenceId
            event.recurrenceDay = day_start.timestamp()

        return event, todo, goal

    @staticmethod
    def from_sql_res(src: dict):
        return Recurrence(
            recurrenceId=src[RECURRENCE_ID],
            userId=src[USER_ID],
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