# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional
import datetime
from models.SQLColumnNames import *


class CalendarEvent(BaseModel):
    eventId: Optional[int]
    userId: Optional[int]
    name: Optional[str]
    description: Optional[str]
    isHidden: Optional[bool] = False  # we use hidden events when completing todo items but don't want it to appear on calendar

    startInstant: Optional[float]
    endInstant: Optional[float]

    linkedGoalId: Optional[int]
    linkedTodoId: Optional[int]
    recurrenceId: Optional[int]
    recurrenceDay: Optional[float]  # the day of the recurrence instance (user may modify the actual startInstance later, but this value won't change)

    def get_sql_events_insert_query(self):
        return "INSERT INTO events VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (None,
                self.userId,
                self.name,
                self.description,
                self.isHidden,
                self.startInstant,
                self.endInstant,

                self.linkedGoalId,
                self.linkedTodoId,
                self.recurrenceId,
                self.recurrenceDay)

    def get_sql_events_in_day_insert_query_and_params(self):
        days = CalendarEvent.get_days_in_range(self.startInstant, self.endInstant)
        values_str = ""
        for day in days:
            values_str += (",(%s, %s, %s)" % day, self.eventId, self.userId)
        return "INSERT INTO events_in_day VALUES (day, event_id, user_id) VALUES %s, ;", (values_str[1:])

    @staticmethod
    def get_days_in_range(start: float, end: float):  # is inclusive
        if end < start:
            raise Exception()
        dt = datetime.datetime.fromtimestamp(start).replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = datetime.datetime.fromtimestamp(end)
        days = []
        while dt <= end_dt:
            days.append(dt.timestamp())
            dt += datetime.timedelta(days=1)
        return [days]

    @staticmethod
    def from_sql_res(src: dict):
        return CalendarEvent(
            eventId=src["event_id"],
            userId=src[USER_ID],
            name=src[NAME],
            description=src[DESCRIPTION],
            isHidden=src[IS_HIDDEN],
            startInstant=src[START_INSTANT],
            endInstant=src[END_INSTANT],

            linkedGoalId=src[LINKED_GOAL_ID],
            linkedTodoId=src[LINKED_TODO_ID],
            recurrenceId=src[RECURRENCE_ID],
            recurrenceDay=src[RECURRENCE_DAY]
        )
