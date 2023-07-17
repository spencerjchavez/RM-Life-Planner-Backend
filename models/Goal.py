# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Optional
from pydantic import BaseModel
from enum import Enum


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
    endInstant: Optional[float] # null == goal is indefinite. This parameter is overridden by timeframe in recurring goals
    # recurring goal stuff
    recurrenceId: Optional[int]
    timeframe: Optional[Timeframe]

    def get_sql_insert_query(self):
        return "INSERT INTO goals (%s, %s, %s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (self.desireId,
             self.userId,
             self.name,
             self.howMuch,
             self.measuringUnits,
             self.startInstant,
             self.endInstant,
             self.recurrenceId,
             self.timeframe)
