# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

from pydantic import BaseModel
from pydantic.class_validators import Optional


class Action(BaseModel):
    planId: Optional[int]  # every action should have a plan which it fulfills
    eventId: Optional[int]
    goalId: Optional[int]
    userId: Optional[int]
    successful: Optional[int]
    howMuchAccomplished: Optional[int]
    notes: Optional[str]
