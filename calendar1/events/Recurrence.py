from pydantic import BaseModel
from pydantic.config import Optional
from typing_extensions import Any


class Recurrence(BaseModel):
    recurrence_id: Optional[int]
    user_id: Optional[int]
    rruleString: str
    monthyears_buffered: Optional[bytes]

    create_todos: Optional[bool]
    todo_name: Optional[str]
    todo_timeframe: Optional[int]

    create_events: Optional[bool]
    event_type: Optional[int]
    event_name: Optional[str]
    event_description: Optional[str]
