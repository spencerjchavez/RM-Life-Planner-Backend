from pydantic import BaseModel
from typing_extensions import Any


class CalendarEvent(BaseModel):
    def __init__(self, name: str, description: str, start_time: int, end_time: int, start_day: int, duration: int,
                 rrule: str, is_in_past: bool, happened: bool, report: str, event_type: int, user_event_id: int,
                 **data: Any):
        super().__init__(**data)
        self.name = name
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.start_day = start_day
        self.duration = duration
        self.rrule = rrule
        self.is_in_past = is_in_past
        self.happened = happened
        self.report = report
        self.event_type = event_type
        self.user_event_id = user_event_id
