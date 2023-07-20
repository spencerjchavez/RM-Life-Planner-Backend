# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Any, Dict, Optional
from pydantic import BaseModel
from models.CalendarEvent import CalendarEvent
from enum import Enum
import datetime
from dateutil.relativedelta import relativedelta


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
    timeframe: Optional[Timeframe]
    startInstant: Optional[float]

    recurrenceId: Optional[int]
    linkedGoalId: Optional[int]

    def get_sql_insert_query(self):
        return "INSERT INTO todos VALUES (%s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (None,
                self.userId,
                self.name,
                self.timeframe,
                self.startInstant,
                self.recurrenceId,
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
