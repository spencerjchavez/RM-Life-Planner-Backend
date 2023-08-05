# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Any, Dict, Optional
from pydantic import BaseModel
from models.CalendarEvent import CalendarEvent
from enum import Enum
import datetime
from dateutil.relativedelta import relativedelta
from models.SQLColumnNames import *


class ToDo(BaseModel):

    todoId: Optional[str]
    userId: Optional[int]

    name: Optional[str]
    startInstant: Optional[float]
    endInstant: Optional[float]  # overridden by timeframe in recurring ToDos

    recurrenceId: Optional[int]
    recurrenceDay: Optional[float]  # the day of the recurrence instance (user may modify the actual startInstance later, but this value won't change)
    linkedGoalId: Optional[int]

    def get_sql_insert_query(self):
        return "INSERT INTO todos VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (None,
                self.userId,
                self.name,
                self.startInstant,
                self.endInstant,
                self.recurrenceId,
                self.recurrenceDay,
                self.linkedGoalId)

    def get_sql_todos_in_day_insert_query_and_params(self):
        if self.endInstant is None:
            raise ValueError()
        days = CalendarEvent.get_days_in_range(self.startInstant, self.endInstant)
        values_str = ""
        for day in days:
            values_str += f"({day}, {self.todoId}, {self.userId}) "
        return "INSERT INTO todos_in_day VALUES (day, todo_id, user_id) VALUES %s, ;", values_str[1:]

    @staticmethod
    def from_sql_res(src: dict):
        return ToDo(todoId=src["todo_id"],
                    userID=src[USER_ID],
                    name=src[NAME],
                    startInstant=src[START_INSTANT],
                    endInstant=src[END_INSTANT],
                    recurrenceId=src[RECURRENCE_ID],
                    recurrenceDay=src[RECURRENCE_DAY],
                    linkedGoalId=src[LINKED_GOAL_ID]
                    )
