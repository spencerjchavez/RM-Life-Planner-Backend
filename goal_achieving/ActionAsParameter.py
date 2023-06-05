from pydantic import BaseModel
from pydantic.class_validators import Optional


class ActionAsParameter(BaseModel):
    event_id: Optional[int]
    plan_id: Optional[int]  # every action should have a plan which it fulfills
    goal_id: Optional[int]
    success: Optional[int]
    how_much_accomplished: Optional[int]
    notes: Optional[str]
