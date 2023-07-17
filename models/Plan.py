# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Optional
from pydantic import BaseModel


class Plan(BaseModel):
    planId: Optional[int]
    userId: Optional[int]
    goalId: Optional[int]
    eventId: Optional[int]
    howMuch: Optional[int]

    def get_sql_insert_query(self):
        return "INSERT INTO plans (%s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (self.userId,
             self.goalId,
             self.eventId,
             self.howMuch)
