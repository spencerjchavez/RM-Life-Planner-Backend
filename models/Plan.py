# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Optional
from pydantic import BaseModel
from models.SQLColumnNames import *


class Plan(BaseModel):
    planId: Optional[int]
    userId: Optional[int]
    goalId: Optional[int]
    eventId: Optional[int]
    howMuch: Optional[float]

    def get_sql_insert_query(self):
        return "INSERT INTO plans VALUES (%s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (None,
                self.userId,
                self.goalId,
                self.eventId,
                self.howMuch)

    @staticmethod
    def from_sql_res(src: dict):
        return Plan(
            planId=src["plan-id"],
            userId=src[USER_ID],
            goalId=src[GOAL_ID],
            eventId=src["event_id"],
            howMuch=src[HOW_MUCH])