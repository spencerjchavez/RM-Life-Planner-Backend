from pydantic import BaseModel
from pydantic.class_validators import Optional


class PlanAsParameter(BaseModel):
    name: Optional[str]
    category: Optional[int]
    priority_level: Optional[int]
    rrule_string: Optional[str]