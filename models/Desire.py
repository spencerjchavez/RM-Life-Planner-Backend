# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Optional
from pydantic import BaseModel
from models.SQLColumnNames import *


class Desire(BaseModel):
    desireId: Optional[int]
    name: Optional[str]
    userId: Optional[int]
    dateCreated: Optional[float]
    deadline: Optional[float]
    dateRetired: Optional[float]
    priorityLevel: Optional[int]
    colorR: Optional[float]
    colorG: Optional[float]
    colorB: Optional[float]

    def get_sql_insert_query(self):
        return "INSERT INTO desires VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (None,
                self.name,
                self.userId,
                self.dateCreated,
                self.deadline,
                self.dateRetired,
                self.priorityLevel,
                self.colorR,
                self.colorG,
                self.colorB)

    @staticmethod
    def from_sql_res(src: dict):
        return Desire(
            desireId=src[DESIRE_ID],
            name=src[NAME],
            userId=src[USER_ID],
            dateCreated=src[DATE_CREATED],
            deadline=src[DEADLINE],
            dateRetired=src[DATE_RETIRED],
            priorityLevel=src[PRIORITY_LEVEL],
            colorR=src[COLOR_R],
            colorG=src[COLOR_G],
            colorB=src[COLOR_B]
        )
