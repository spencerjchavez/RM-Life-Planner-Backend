# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Optional
from pydantic import BaseModel


class Action(BaseModel):
    planId: Optional[int]  # every action should have a plan which it fulfills
    eventId: Optional[int]
    goalId: Optional[int]
    userId: Optional[int]
    successful: Optional[int]
    howMuchAccomplished: Optional[int]
    notes: Optional[str]

    def get_sql_insert_query(self):
        return "INSERT INTO actions (%s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (self.planId,
                self.eventId,
                self.goalId,
                self.userId,
                self.successful,
                self.howMuchAccomplished,
                self.notes)
