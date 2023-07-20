# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Optional
from pydantic import BaseModel
from enum import Enum


class Action(BaseModel):

    class Success(Enum):
        UNKNOWN = 0
        SUCCESSFUL = 1
        UNSUCCESSFUL = 2
        PARTIAL = 3

    planId: Optional[int]  # every action should have a plan which it fulfills
    eventId: Optional[int]
    goalId: Optional[int]
    userId: Optional[int]
    successful: Optional[int]
    howMuchAccomplished: Optional[int]
    notes: Optional[str]

    def get_sql_insert_query(self):
        return "INSERT INTO actions VALUES (%s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (self.planId,
                self.eventId,
                self.goalId,
                self.userId,
                self.successful,
                self.howMuchAccomplished,
                self.notes)
