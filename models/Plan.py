# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

from pydantic import BaseModel
from pydantic.class_validators import Optional


class Plan(BaseModel):
    planId: Optional[int]
    userId: Optional[int]
    goalId: Optional[int]
    eventId: Optional[int]
    howMuch: Optional[int]
