from pydantic import BaseModel
from pydantic.class_validators import Optional


class Desire(BaseModel):
    desire_id: Optional[int]
    user_id: Optional[int]
    name: Optional[str]
    category_id: Optional[int]
    priority_level: Optional[int]
    deadline_date: Optional[int]  # when the desire should be realized [ex. get a job within a year]
    related_goal_ids: Optional[str]