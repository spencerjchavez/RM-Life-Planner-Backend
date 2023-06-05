from pydantic import BaseModel
from pydantic.fields import Optional


class DesireAsParameter(BaseModel):
    name: Optional[str]
    user_id: Optional[int]
    categoryId: Optional[int]
    priorityLevel: Optional[int]
    deadlineDate: Optional[int]  # when the desire should be realized [ex. get a job within a year)
    relatedGoalIds: Optional[str]