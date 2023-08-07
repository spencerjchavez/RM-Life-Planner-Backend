# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Optional
from pydantic import BaseModel
from models.SQLColumnNames import *
from models.CalendarEvent import CalendarEvent
import datetime


class Goal(BaseModel):

    goalId: Optional[int]
    desireId: Optional[int]
    userId: Optional[int]
    name: Optional[str]
    howMuch: Optional[float]
    measuringUnits: Optional[str]
    startInstant: Optional[float]
    endInstant: Optional[float]  # null == goal is indefinite. This parameter is overridden by timeframe in recurring goals
    # recurring goal stuff
    recurrenceId: Optional[int]
    recurrenceDay: Optional[float]  # the day of the recurrence instance (user may modify the actual startInstance later, but this value won't change)

    def get_sql_insert_query(self):
        return "INSERT INTO goals VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (None,
                self.desireId,
                self.userId,
                self.name,
                self.howMuch,
                self.measuringUnits,
                self.startInstant,
                self.endInstant,
                self.recurrenceId,
                self.recurrenceDay)

    def get_sql_goals_in_day_insert_query_and_params(self):
        if self.endInstant is None:
            raise ValueError()
        days = CalendarEvent.get_days_in_range(self.startInstant, self.endInstant)
        values_str = ""
        for day in days:
            values_str += (",(%s, %s, %s)" % day, self.goalId, self.userId)
        return "INSERT INTO events_in_day (day, event_id, user_id) VALUES %s ;", (values_str[1:])

    @staticmethod
    def from_sql_res(src: dict):
        return Goal(
            goalId=src[GOAL_ID],
            desireId=src[DESIRE_ID],
            userId=src[USER_ID],
            name=src[NAME],
            howMuch=src[HOW_MUCH],
            measuringUnits=src[MEASURING_UNITS],
            startInstant=src[START_INSTANT],
            endInstant=src[END_INSTANT],
            recurrenceId=src[RECURRENCE_ID],
            recurrenceDay=src[RECURRENCE_DAY]
        )
