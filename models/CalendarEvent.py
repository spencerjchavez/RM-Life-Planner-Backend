# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

from pydantic import BaseModel
from typing import Optional
import datetime


class CalendarEvent(BaseModel):

    eventId: Optional[int]
    userId: Optional[int]
    name: Optional[str]
    description: Optional[str]
    isHidden: Optional[bool] = False # we use hidden events when completing todo items but don't want it to appear on calendar

    startInstant: Optional[float]
    endInstant: Optional[float]
    duration: Optional[float]  # client does not pass this

    linkedGoalId: Optional[int]
    linkedTodoId: Optional[int]
    recurrenceId: Optional[int]

    def get_sql_events_insert_query(self):
        return "INSERT INTO events (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (self.userId,
             self.name,
             self.description,
             self.isHidden,
             self.startInstant,
             self.endInstant,
             self.duration,

             self.linkedGoalId,
             self.linkedTodoId,
             self.recurrenceId)

    def get_sql_events_in_day_insert_query_and_params(self):
        days = CalendarEvent.get_days_in_range(self.startInstant, self.endInstant)
        values_str = ""
        for day in days:
            values_str += (",(%s, %s, %s)" % day, self.eventId, self.userId)
        return "INSERT INTO events_in_day (day, event_id, user_id) VALUES %s, ;", (values_str[1:])

    @staticmethod
    def get_days_in_range(start: float, end: float):  # is inclusive
        dt = datetime.datetime.fromtimestamp(start).replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = datetime.datetime.fromtimestamp(end)
        days = []
        while dt <= end_dt:
            days.append(dt.timestamp())
            dt += datetime.timedelta(days=1)
        return [days]
