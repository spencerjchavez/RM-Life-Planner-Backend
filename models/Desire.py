# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Optional
from pydantic import BaseModel


class Desire(BaseModel):
    desireId: Optional[int]
    name: Optional[str]
    userId: Optional[int]
    dateCreated: Optional[float]
    deadline: Optional[float]
    dateRetired: Optional[float]
    priorityLevel: Optional[int]
    colorR: Optional[int]
    colorG: Optional[int]
    colorB: Optional[int]

    def get_sql_insert_query(self):
        return "INSERT INTO desires (%s, %s, %s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (self.name,
             self.userId,
             self.dateCreated,
             self.deadline,
             self.dateRetired,
             self.priorityLevel,
             self.colorR,
             self.colorG,
             self.colorB)

