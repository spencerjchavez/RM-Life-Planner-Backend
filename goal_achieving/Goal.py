from pydantic import BaseModel
from pydantic.class_validators import Optional


class Goal(BaseModel):
    goal_id: Optional[int]
    desire_id: Optional[int]
    user_id: Optional[int]
    name: Optional[str]
    how_much: Optional[int]
    measuring_units: Optional[str]
    # if is recurring goal
    rrule_string: Optional[str]
    recurrence_id: Optional[int]
    # if one-time goal
    plan_id: Optional[int]


