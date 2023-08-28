# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Optional
from pydantic import BaseModel
from app.extras.SQLColumnNames import *


class ToDo(BaseModel):

    todoId: Optional[int]
    userId: Optional[int]

    name: Optional[str]
    startDate: Optional[str]
    deadlineDate: Optional[str]  # the deadline we want to complete it by
    howMuchPlanned: Optional[float]

    recurrenceId: Optional[int]
    recurrenceDate: Optional[str]  # the day of the recurrence instance (user may modify the actual startInstance later, but this value won't change)
    linkedGoalId: Optional[int]

    def get_sql_insert_query(self):
        return "INSERT INTO todos VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (None,
                self.userId,
                self.name,
                self.startDate,
                self.deadlineDate,
                self.howMuchPlanned,
                self.recurrenceId,
                self.recurrenceDate,
                self.linkedGoalId)
    '''
    def get_sql_todos_in_day_insert_query_and_params(self, completion_instant: float):
        days = CalendarEvent.get_days_in_range(self.startInstant, completion_instant)
        stmt_str = "INSERT INTO todos_in_day (day, todo_id, user_id) VALUES "
        params = ()
        for day in days:
            stmt_str += "(%s, %s, %s),"
            params += (day, self.todoId, self.userId)
        return stmt_str[:len(stmt_str) - 1], params
    '''
    @staticmethod
    def from_sql_res(src: dict):
        src[START_DATE] = src[START_DATE].strftime("%Y-%m-%d")
        if src[DEADLINE_DATE] is not None:
            src[DEADLINE_DATE] = src[DEADLINE_DATE].strftime("%Y-%m-%d")
        if src[RECURRENCE_DATE] is not None:
            src[RECURRENCE_DATE] = src[RECURRENCE_DATE].strftime("%Y-%m-%d")

        return ToDo(todoId=src["todo_id"],
                    userID=src[USER_ID],
                    name=src[NAME],
                    startDate=src[START_DATE],
                    deadlineDate=src[DEADLINE_DATE],
                    howMuchPlanned=src[HOW_MUCH_PLANNED],
                    recurrenceId=src[RECURRENCE_ID],
                    recurrenceDate=src[RECURRENCE_DATE],
                    linkedGoalId=src[LINKED_GOAL_ID]
                    )
