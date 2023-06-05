from pydantic import BaseModel
from pydantic.class_validators import Optional


class ToDo(BaseModel):
    name: Optional[str]
    timeframe: Optional[int] # from TodoTimeframe enum
    todo_id: Optional[int]
    recurrence_id: Optional[int]
    goal_id: Optional[int]
    plan_id: Optional[int]
    action_id: Optional[int]
 