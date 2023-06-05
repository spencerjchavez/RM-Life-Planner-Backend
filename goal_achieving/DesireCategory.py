from pydantic import BaseModel
from pydantic.fields import Optional


class DesireCategory(BaseModel):
    name: Optional[str]
    category_id: Optional[int]
    user_id: Optional[int]
    color_r: Optional[int]
    color_g: Optional[int]
    color_b: Optional[int]
