# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

from pydantic import BaseModel
from pydantic.fields import Optional


class Desire(BaseModel):
    desireId: Optional[int]
    name: Optional[str]
    userId: Optional[int]
    deadline: Optional[int]
    priorityLevel: Optional[int]
    colorR: Optional[int]
    colorG: Optional[int]
    colorB: Optional[int]
