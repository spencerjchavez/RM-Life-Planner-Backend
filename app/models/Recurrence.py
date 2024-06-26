from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.models.Goal import Goal
from app.models.ToDo import ToDo
from app.models.CalendarEvent import CalendarEvent
from app.extras.SQLColumnNames import *
from datetime import datetime
from dateutil import relativedelta


class Recurrence(BaseModel):

    class Timeframe(str, Enum):
        INDEFINITE = 'INDEFINITE'
        DAY = 'DAY'
        WEEK = 'WEEK'
        MONTH = 'MONTH'
        YEAR = 'YEAR'

    recurrenceId: Optional[int] = None
    userId: Optional[int] = None
    rruleString: Optional[str] = None
    startDate: Optional[str] = None
    startTime: Optional[str] = None

    eventName: Optional[str] = None
    eventDescription: Optional[str] = None
    eventDuration: Optional[float] = None

    todoName: Optional[str] = None
    todoTimeframe: Optional[Timeframe] = None
    todoHowMuchPlanned: Optional[float]

    goalName: Optional[str] = None
    goalDesireId: Optional[int] = None
    goalHowMuch: Optional[int] = None
    goalMeasuringUnits: Optional[str] = None
    goalTimeframe: Optional[Timeframe] = None
    goalPriorityLevel: Optional[int] = None

    def get_sql_insert_query(self):
        return "INSERT INTO recurrences VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (None,
                self.userId,
                self.rruleString,
                self.startDate,
                self.startTime,

                self.eventName,
                self.eventDescription,
                self.eventDuration,

                self.todoName,
                self.todoTimeframe,
                self.todoHowMuchPlanned,

                self.goalName,
                self.goalDesireId,
                self.goalHowMuch,
                self.goalMeasuringUnits,
                self.goalTimeframe,
                self.goalPriorityLevel)

    def generate_instance_objects_on_date(self, start_date: datetime):
        recurrence_start_time = datetime.strptime(self.startTime, "%H:%M:%S")
        event_end_datetime = None
        if self.eventDuration is not None:
            event_end_datetime = start_date + relativedelta.relativedelta(seconds=int(self.eventDuration + recurrence_start_time.hour*60*60 + recurrence_start_time.minute*60 + recurrence_start_time.second))
        todo_end_date: datetime
        if self.todoTimeframe == Recurrence.Timeframe.YEAR:
            todo_end_date = start_date + relativedelta.relativedelta(years=1)
        elif self.todoTimeframe == Recurrence.Timeframe.MONTH:
            todo_end_date = start_date + relativedelta.relativedelta(months=1)
        elif self.todoTimeframe == Recurrence.Timeframe.WEEK:
            todo_end_date = start_date + relativedelta.relativedelta(weeks=1)
        else:  # == Timeframe.DAY
            todo_end_date = start_date + relativedelta.relativedelta(days=1)

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
            goal.startDate = start_date.strftime("%Y-%m-%d")
            goal.deadlineDate = todo_end_date.strftime("%Y-%m-%d")
            goal.recurrenceId = self.recurrenceId
            goal.recurrenceDate = start_date.strftime("%Y-%m-%d")
            goal.priorityLevel = self.goalPriorityLevel

        if self.todoName is not None:
            todo = ToDo()
            todo.name = self.todoName
            todo.howMuchPlanned = self.todoHowMuchPlanned
            todo.recurrenceId = self.recurrenceId
            todo.userId = self.userId
            todo.startDate = start_date.strftime("%Y-%m-%d")
            todo.deadlineDate = todo_end_date.strftime("%Y-%m-%d")
            todo.recurrenceDate = start_date.strftime("%Y-%m-%d")

        if self.eventName is not None:
            event = CalendarEvent()
            event.name = self.eventName
            event.description = self.eventDescription
            event.startDate = start_date.strftime("%Y-%m-%d")
            event.startTime = self.startTime
            event.endDate = event_end_datetime.strftime("%Y-%m-%d")
            event.endTime = event_end_datetime.strftime("%H:%M:%S")
            event.userId = self.userId
            event.recurrenceId = self.recurrenceId
            event.recurrenceDate = start_date.strftime("%Y-%m-%d")

        return event, todo, goal

    @staticmethod
    def from_sql_res(src: dict):
        src[START_TIME] = (src[START_DATE] + src[START_TIME]).strftime("%H:%M:%S")
        src[START_DATE] = src[START_DATE].strftime("%Y-%m-%d")
        return Recurrence(
            recurrenceId=src[RECURRENCE_ID],
            userId=src[USER_ID],
            rruleString=src[RRULE_STRING],
            startDate=src[START_DATE],
            startTime=src[START_TIME],

            eventName=src[RECURRENCE_EVENT_NAME],
            eventDescription=src[RECURRENCE_EVENT_DESCRIPTION],
            eventDuration=src[RECURRENCE_EVENT_DURATION],

            todoName=src[RECURRENCE_TODO_NAME],
            todoTimeframe=src[RECURRENCE_TODO_TIMEFRAME],
            todoHowMuchPlanned=src["todo_how_much_planned"],

            goalName=src[RECURRENCE_GOAL_NAME],
            goalDesireId=src[RECURRENCE_GOAL_DESIRE_ID],
            goalHowMuch=src[RECURRENCE_GOAL_HOW_MUCH],
            goalMeasuringUnits=src[RECURRENCE_GOAL_MEASURING_UNITS],
            goalTimeframe=src[RECURRENCE_GOAL_TIMEFRAME],
            goalPriorityLevel=src[RECURRENCE_GOAL_PRIORITY_LEVEL]
        )
