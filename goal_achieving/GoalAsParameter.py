# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

from pydantic import BaseModel
from pydantic.class_validators import Optional


class GoalAsParameter(BaseModel):
    userId: Optional[int]
    desireId: Optional[int]
    planId: Optional[int]  # not included in post calls
    name: Optional[str]
    howMuch: Optional[int]
    measuringUnits: Optional[str]
    rruleString: Optional[str]
    createTodos: Optional[bool]
    createEvents: Optional[bool]