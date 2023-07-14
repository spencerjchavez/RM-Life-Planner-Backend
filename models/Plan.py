# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Optional
from pydantic import BaseModel


class Plan(BaseModel):
    planId: Optional[int]
    userId: Optional[int]
    goalId: Optional[int]
    eventId: Optional[int]
    howMuch: Optional[int]
