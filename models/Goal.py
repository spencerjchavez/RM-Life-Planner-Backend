# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Optional
from pydantic import BaseModel


class Goal(BaseModel):
    goalId: Optional[int]
    userId: Optional[int]
    desireId: Optional[int]
    planId: Optional[int]  # not included in post calls
    name: Optional[str]
    howMuch: Optional[int]
    measuringUnits: Optional[str]
    startInstant: Optional[float]
    endInstant: Optional[float] # null == goal is indefinite. This parameter is overridden by timeframe in recurring goals
    # recurring goal stuff
    recurrenceId: Optional[int]
    timeframe: Optional[int]