# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
import datetime

from pydantic import BaseModel
from typing import Optional
from extras.SQLColumnNames import *


class CalendarEvent(BaseModel):
    eventId: Optional[int]
    userId: Optional[int]
    name: Optional[str]
    description: Optional[str]
    isHidden: Optional[bool] = False  # we use hidden events when completing todoitems but don't want it to appear on calendar

    startDate: Optional[str]
    startTime: Optional[str]
    endDate: Optional[str]
    endTime: Optional[str]

    linkedTodoId: Optional[int]
    linkedGoalId: Optional[int]
    howMuchAccomplished: Optional[float]
    notes: Optional[str]

    recurrenceId: Optional[int]
    recurrenceDate: Optional[str]  # the day of the recurrence instance (user may modify the actual startInstance later, but this value won't change)

    def get_sql_events_insert_query(self):
        return "INSERT INTO events VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (None,
                self.userId,
                self.name,
                self.description,
                self.isHidden,
                self.startDate,
                self.startTime,
                self.endDate,
                self.endTime,

                self.linkedTodoId,
                self.linkedGoalId,
                self.howMuchAccomplished,
                self.notes,

                self.recurrenceId,
                self.recurrenceDate)

    '''
    @staticmethod
    def get_days_in_range(start: float, end: float):  # is inclusive
        if end < start:
            raise Exception()
        dt = datetime.datetime.fromtimestamp(start, tzinfo).replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = datetime.datetime.fromtimestamp(end, tzinfo).replace(hour=0, minute=0, second=0, microsecond=0)
        days = []
        while dt <= end_dt:
            days.append(dt.timestamp())
            dt += datetime.timedelta(days=1)
        return days
    '''
    @staticmethod
    def from_sql_res(src: dict):
        src[START_DATE] = src[START_DATE].strftime("%Y-%m-%d")
        src[END_DATE] = src[END_DATE].strftime("%Y-%m-%d")
        start_dt = datetime.datetime(year=2000, month=1, day=1) + src[START_TIME]  # use datetime object so that we can convert time delta into datetime and then use .strftime()
        src[START_TIME] = start_dt.strftime("%H:%M:%S")
        end_dt = datetime.datetime(year=2000, month=1, day=1) + src[END_TIME]
        src[END_TIME] = end_dt.strftime("%H:%M:%S")
        if src[RECURRENCE_DATE] is not None:
            src[RECURRENCE_DATE] = src[RECURRENCE_DATE].strftime("%Y-%m-%d")
        return CalendarEvent(
            eventId=src["event_id"],
            userId=src[USER_ID],
            name=src[NAME],
            description=src[DESCRIPTION],
            isHidden=src[IS_HIDDEN],
            startDate=src[START_DATE],
            startTime=src[START_TIME],
            endDate=src[END_DATE],
            endTime=src[END_TIME],

            linkedTodoId=src[LINKED_TODO_ID],
            linkedGoalId=src[LINKED_GOAL_ID],
            howMuchAccomplished=src[HOW_MUCH_ACCOMPLISHED],
            notes=src[NOTES],

            recurrenceId=src[RECURRENCE_ID],
            recurrenceDate=src[RECURRENCE_DATE]
        )
