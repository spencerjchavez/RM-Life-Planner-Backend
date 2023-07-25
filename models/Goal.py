# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Optional
from pydantic import BaseModel
from enum import Enum
from models.SQLColumnNames import *


class Goal(BaseModel):
    class Timeframe(Enum):
        INDEFINITE = 0
        DAY = 1
        WEEK = 2
        MONTH = 3
        YEAR = 4

    goalId: Optional[int]
    desireId: Optional[int]
    userId: Optional[int]
    name: Optional[str]
    howMuch: Optional[int]
    measuringUnits: Optional[str]
    startInstant: Optional[float]
    endInstant: Optional[
        float]  # null == goal is indefinite. This parameter is overridden by timeframe in recurring goals
    # recurring goal stuff
    recurrenceId: Optional[int]
    timeframe: Optional[Timeframe]

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
                self.timeframe)

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
            timeframe=src[TIMEFRAME]
        )
