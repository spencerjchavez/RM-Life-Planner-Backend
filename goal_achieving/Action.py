from pydantic import BaseModel
from pydantic.class_validators import Optional


class Action(BaseModel):
    action_id: Optional[int]
    event_id: Optional[int]
    plan_id: Optional[int]
    goal_id: Optional[int]
    success: Optional[int]
    how_much_accomplished: Optional[int]
    notes: Optional[str]
