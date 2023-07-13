# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

from pydantic import BaseModel
from pydantic.class_validators import Optional


class Goal(BaseModel):
    goalId: Optional[int]
    userId: Optional[int]
    desireId: Optional[int]
    planId: Optional[int]  # not included in post calls
    name: Optional[str]
    howMuch: Optional[int]
    measuringUnits: Optional[str]
    startInstant: Optional[str]
    endInstant: Optional[str] # null == goal is indefinite. This parameter is overridden by timeframe in recurring goals
    # recurring goal stuff
    recurrenceId: Optional[int]
    timeframe: Optional[int]