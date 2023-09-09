# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Optional
from pydantic import BaseModel
from app.extras.SQLColumnNames import *


class Desire(BaseModel):
    desireId: Optional[int]
    name: Optional[str]
    userId: Optional[int]
    dateCreated: Optional[str]
    deadline: Optional[str]
    dateRetired: Optional[str]
    priorityLevel: Optional[int]
    #colorR: Optional[float]
    #colorG: Optional[float]
    #colorB: Optional[float]

    def get_sql_insert_query(self):
        return "INSERT INTO desires VALUES (%s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (None,
                self.name,
                self.userId,
                self.dateCreated,
                self.deadline,
                self.dateRetired,
                self.priorityLevel)

    @staticmethod
    def from_sql_res(src: dict):
        if src[DATE_CREATED] is not None:
            src[DATE_CREATED] = src[DATE_CREATED].strftime("%Y-%m-%d")
        if src[DEADLINE] is not None:
            src[DEADLINE] = src[DEADLINE].strftime("%Y-%m-%d")
        if src[DATE_RETIRED] is not None:
            src[DATE_RETIRED] = src[DATE_RETIRED].strftime("%Y-%m-%d")
        return Desire(
            desireId=src[DESIRE_ID],
            name=src[NAME],
            userId=src[USER_ID],
            dateCreated=src[DATE_CREATED],
            deadline=src[DEADLINE],
            dateRetired=src[DATE_RETIRED],
            priorityLevel=src[PRIORITY_LEVEL]
        )
