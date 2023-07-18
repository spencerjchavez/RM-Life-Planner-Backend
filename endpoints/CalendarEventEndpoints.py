import datetime
import json
from datetime import datetime
from typing import Optional

import fastapi
from fastapi import APIRouter, HTTPException
from mysql.connector.cursor import MySQLCursor
from models.CalendarEvent import CalendarEvent
from endpoints import UserEndpoints
from models.Authentication import Authentication
from endpoints.MonthsAccessedByUserEndpoints import MonthsAccessedByUser
from models.SQLColumnNames import SQLColumnNames as _


class CalendarEventEndpoints:
    # TODO: make sure IN ALL ENDPOINTS when a user creates a resource the user_id matches

    router = APIRouter()
    cursor: MySQLCursor

    @staticmethod
    @router.post("/api/calendar/events")
    def create_calendar_event(authentication: Authentication, event: CalendarEvent):
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)

        CalendarEventEndpoints.cursor.execute(
            event.get_sql_events_insert_query(),
            event.get_sql_insert_params())

        # insert into events_by_user_day
        stmt, params = event.get_sql_events_in_day_insert_query_and_params()
        CalendarEventEndpoints.cursor.execute(stmt, params)
        return {"message": "event successfully added", "event_id": event.eventId}, 200

    @staticmethod
    @router.get("/api/calendar/events")
    def get_calendar_event(authentication: Authentication, event_id: int):
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        CalendarEventEndpoints.cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
        res = CalendarEventEndpoints.cursor.fetchone()
        if res["user_id"] != authentication.user_id:
            raise HTTPException(detail="User is not authenticated to access this resource", status_code=401)
        return res, 200

    @staticmethod
    @router.get("/api/calendar/events")
    def get_calendar_events(authentication: Authentication, start_day: float, end_day: Optional[float] = None):
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        if end_day is None:
            end_day = start_day
        dt = datetime.fromtimestamp(start_day)
        event_ids = set()
        while dt.timestamp() <= end_day:
            dt.replace(hour=0, minute=0, second=0, microsecond=0)
            year = dt.year
            month = dt.month
            # register that we are accessing month to generate recurrence events
            MonthsAccessedByUser.register_month_accessed_by_user(authentication, year, month)
            CalendarEventEndpoints.cursor.execute("SELECT event_id FROM events_in_day WHERE day = %s AND user_id = %s",
                                                  (dt.timestamp(), authentication.user_id))
            res = CalendarEventEndpoints.cursor.fetchall()
            for row in res:
                event_ids.add(row["event_id"])
            dt += datetime.timedelta(days=1)

        stmt = ""
        for event_id in event_ids:
            stmt += f"SELECT * FROM events WHERE event_id = {event_id};"
        CalendarEventEndpoints.cursor.execute(stmt, multi=True)
        res = CalendarEventEndpoints.cursor.fetchall()
        return {"events": res}, 200

    @staticmethod
    @router.put("/api/calendar/events/{event_id}")
    def update_calendar_event(authentication: Authentication, event_id: int, event: CalendarEvent):
        res = CalendarEventEndpoints.get_calendar_event(authentication, event_id)
        time_changed = False
        if res["start_instant"] != event.startInstant or res["end_instant"] != event.endInstant:
            time_changed = True
        CalendarEventEndpoints.cursor.execute("UPDATE events SET %s = %s, %s = %s, %s = %s, %s = %s, %s = %s, %s = %s, %s = %s, %s = %s WHERE event_id = %s",
                                              (_.NAME, event.name,
                                               _.DESCRIPTION, event.description,
                                               _.IS_HIDDEN, event.isHidden,
                                               _.START_INSTANT, event.startInstant,
                                               _.END_INSTANT, event.endInstant,
                                               _.DURATION, event.duration,
                                               _.LINKED_GOAL_ID, event.linkedGoalId,
                                               _.LINKED_TODO_ID, event.linkedTodoId,
                                               event_id))
        if time_changed:
            CalendarEventEndpoints.cursor.execute("DELETE FROM events_in_day WHERE event_id = %s", (event_id,))
            query, params = event.get_sql_events_in_day_insert_query_and_params()
            CalendarEventEndpoints.cursor.execute(query, params)  # add back to events_in_day

        # yuhhhhhh
        return 200

    @staticmethod
    @router.delete("/api/calendar/events/{event_id}")
    def delete_event(authentication: Authentication, event_id: int):
        CalendarEventEndpoints.get_calendar_event(authentication, event_id)  # authenticate
        CalendarEventEndpoints.cursor.execute("DELETE FROM events WHERE event_id = %s", (event_id,))
        CalendarEventEndpoints.cursor.execute("DELETE FROM events_in_day WHERE event_id = %s", (event_id,))
        return f"successfully deleted event with id: '{event_id}'", 200

    @staticmethod
    @router.delete("/api/calendar/events")
    def delete_events_of_user(authentication: Authentication):
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        CalendarEventEndpoints.cursor.execute("DELETE FROM events WHERE user_id = %s", (authentication.user_id,))
        CalendarEventEndpoints.cursor.execute("DELETE FROM events_in_day WHERE user_id = %s", (authentication.user_id,))
