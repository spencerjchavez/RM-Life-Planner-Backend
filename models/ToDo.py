# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Any, Dict, Optional
from pydantic import BaseModel
from models.CalendarEvent import CalendarEvent
from enum import Enum
import datetime
from dateutil.relativedelta import relativedelta
from models.SQLColumnNames import *


class ToDo(BaseModel):
    class Timeframe(Enum):
        INDEFINITE = 0
        DAY = 1
        WEEK = 2
        MONTH = 3
        YEAR = 4

    todoId: Optional[str]
    userId: Optional[int]

    name: Optional[str]
    startInstant: Optional[float]
    deadline: Optional[float]  # overridden by timeframe in recurring ToDos

    recurrenceId: Optional[int]
    timeframe: Optional[Timeframe]
    linkedGoalId: Optional[int]

    def get_sql_insert_query(self):
        return "INSERT INTO todos VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (None,
                self.userId,
                self.name,
                self.startInstant,
                self.deadline,
                self.recurrenceId,
                self.timeframe,
                self.linkedGoalId)

    def get_sql_todos_in_day_insert_query_and_params(self):
        # INDEFINITE timeframe todos do not appear in todos_in_day, as they are not bounded to any timeframe, but will simply disappear when they are completed
        if self.timeframe == self.Timeframe.INDEFINITE:
            return
        end_instant: datetime
        if self.timeframe == self.Timeframe.DAY:
            end_instant = datetime.datetime.fromtimestamp(self.startInstant) + datetime.timedelta(days=1)
        elif self.timeframe == self.Timeframe.WEEK:
            end_instant = datetime.datetime.fromtimestamp(self.startInstant) + datetime.timedelta(days=7)
        elif self.timeframe == self.Timeframe.MONTH:
            end_instant = datetime.datetime.fromtimestamp(self.startInstant) + relativedelta(months=1)
        else:  # self.timeframe == self.Timeframe.YEAR:
            end_instant = datetime.datetime.fromtimestamp(self.startInstant) + relativedelta(years=1)
        days = CalendarEvent.get_days_in_range(self.startInstant, end_instant.timestamp())
        values_str = ""
        for day in days:
            values_str += f"({day}, {self.todoId}, {self.userId}) "
        return "INSERT INTO events_in_day VALUES (day, event_id, user_id) VALUES %s, ;", values_str[1:]

    @staticmethod
    def from_sql_res(src: dict):
        return ToDo(todoId=src["todo_id"],
                    userID=src[USER_ID],
                    name=src[NAME],
                    startInstant=src[START_INSTANT],
                    deadline=src[DEADLINE],
                    recurrenceId=src[RECURRENCE_ID],
                    timeframe=src[TIMEFRAME],
                    linkedGoalId=src[LINKED_GOAL_ID])
