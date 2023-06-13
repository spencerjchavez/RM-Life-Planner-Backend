# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

from pydantic import BaseModel
from pydantic.fields import Optional


class DesireCategoryAsParameter(BaseModel):
    name: Optional[str]
    userId: Optional[int]
    # colors are in the range of 0.0 to 1.0
    colorR: Optional[float]
    colorB: Optional[float]
    colorG: Optional[float]
