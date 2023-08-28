# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Optional
from pydantic import BaseModel
from app.extras.SQLColumnNames import *


class Goal(BaseModel):

    goalId: Optional[int]
    desireId: Optional[int]
    userId: Optional[int]
    name: Optional[str]
    howMuch: Optional[float]
    measuringUnits: Optional[str]
    startDate: Optional[str]
    deadlineDate: Optional[str]  # deadline to complete goal by. null = no deadline
    # recurring goal stuff
    recurrenceId: Optional[int]
    recurrenceDate: Optional[str]  # the day of the recurrence instance (user may modify the actual startInstance later, but this value won't change)

    def get_sql_insert_query(self):
        return "INSERT INTO goals VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (None,
                self.desireId,
                self.userId,
                self.name,
                self.howMuch,
                self.measuringUnits,
                self.startDate,
                self.deadlineDate,
                self.recurrenceId,
                self.recurrenceDate)

    '''
    def get_sql_goals_in_day_insert_query_and_params(self, completion_instant: float):
        days = CalendarEvent.get_days_in_range(self.startInstant, completion_instant)
        stmt_str = "INSERT INTO goals_in_day (day, goal_id, user_id) VALUES "
        params = ()
        for day in days:
            stmt_str += "(%s, %s, %s),"
            params += (day, self.goalId, self.userId)
        return stmt_str[:len(stmt_str)-1], params
    '''
    @staticmethod
    def from_sql_res(src: dict):
        src[START_DATE] = src[START_DATE].strftime("%Y-%m-%d")
        if src[DEADLINE_DATE] is not None:
            src[DEADLINE_DATE] = src[DEADLINE_DATE].strftime("%Y-%m-%d")
        if src[RECURRENCE_DATE] is not None:
            src[RECURRENCE_DATE] = src[RECURRENCE_DATE].strftime("%Y-%m-%d")

        return Goal(
            goalId=src[GOAL_ID],
            desireId=src[DESIRE_ID],
            userId=src[USER_ID],
            name=src[NAME],
            howMuch=src[HOW_MUCH],
            measuringUnits=src[MEASURING_UNITS],
            startDate=src[START_DATE],
            deadlineDate=src[DEADLINE_DATE],
            recurrenceId=src[RECURRENCE_ID],
            recurrenceDate=src[RECURRENCE_DATE]
        )
