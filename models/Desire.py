# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Optional
from pydantic import BaseModel


class Desire(BaseModel):
    desireId: Optional[int]
    name: Optional[str]
    userId: Optional[int]
    deadline: Optional[int]
    priorityLevel: Optional[int]
    colorR: Optional[int]
    colorG: Optional[int]
    colorB: Optional[int]
