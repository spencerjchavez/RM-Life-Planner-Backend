from pydantic import BaseModel
from pydantic.class_validators import Optional


class GoalAsParameter(BaseModel):
    userId: Optional[int]
    desireId: Optional[int]
    name: Optional[str]
    howMuch: Optional[int]
    measuringUnits: Optional[str]
    rruleString: Optional[str]