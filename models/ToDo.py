# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Any, Dict

from pydantic import BaseModel
from pydantic.class_validators import Optional


class ToDo(BaseModel):
    toDoId: Optional[str]
    userId: Optional[int]

    name: Optional[str]
    timeframe: Optional[int]
    startInstant: Optional[float]

    recurrenceId: Optional[int]
    linkedGoalId: Optional[int]

    def __init__(self, vals: Dict[str, str]):
        super().__init__()
        self.name = vals["name"]
        self.timeFrame = int(vals["timeFrame"])
        self.startDay = float(vals["startDay"])
        self.recurrenceId = int(vals["recurrenceId"])
        self.userId = int(vals["userId"])
        self.goalId = int(vals["goalId"])
        self.planId = int(vals["planId"])
        self.actionId = int(vals["actionId"])
