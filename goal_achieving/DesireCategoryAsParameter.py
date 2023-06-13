# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

from pydantic import BaseModel
from pydantic.fields import Optional


class DesireCategoryAsParameter(BaseModel):
    name: Optional[str]
    userId: Optional[int]
    colorR: Optional[int]
    colorB: Optional[int]
    colorG: Optional[int]
