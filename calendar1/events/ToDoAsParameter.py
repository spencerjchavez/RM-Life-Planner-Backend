# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

from pydantic import BaseModel
from pydantic.class_validators import Optional


class ToDoAsParameter(BaseModel):
    name: Optional[str]
    timeframe: Optional[int]  # from TodoTimeframe enum
    recurrence_id: Optional[int]
    goal_id: Optional[int]
    plan_id: Optional[int]
    action_id: Optional[int]
