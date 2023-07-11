# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

from pydantic import BaseModel
from pydantic.class_validators import Optional

class PlanAsParameter(BaseModel):
    userId: Optional[int]
    goalId: Optional[int]
    eventId: Optional[int]
    todoId: Optional[int]
    planDescription: Optional[str]
    actionId: Optional[str]
    howMuch: Optional[int]
