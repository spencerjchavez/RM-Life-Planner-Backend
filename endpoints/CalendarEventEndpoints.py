import datetime
from datetime import datetime
from typing import Optional
import mysql
from fastapi import APIRouter, HTTPException
from mysql.connector.cursor import MySQLCursor, Error
from models.CalendarEvent import CalendarEvent
from models.Authentication import Authentication
from models.SQLColumnNames import SQLColumnNames as _
from endpoints import UserEndpoints, RecurrenceEndpoints


# TODO: make sure IN ALL ENDPOINTS when a user creates a resource the user_id matches

router = APIRouter()
cursor: MySQLCursor


@router.post("/api/calendar/events")
def create_calendar_event(authentication: Authentication, event: CalendarEvent):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    cursor.execute(
        event.get_sql_events_insert_query(),
        event.get_sql_insert_params())
    # insert into events_by_user_day
    stmt, params = event.get_sql_events_in_day_insert_query_and_params()
    cursor.execute(stmt, params)
    return {"message": "event successfully added", "event_id": event.eventId}


@router.get("/api/calendar/events")
def get_calendar_event(authentication: Authentication, event_id: int):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
    res = cursor.fetchone()
    if res["user_id"] != authentication.user_id:
        raise HTTPException(detail="User is not authenticated to access this resource", status_code=401)
    return res


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
        RecurrenceEndpoints.register_month_accessed_by_user(authentication, year, month)
        cursor.execute("SELECT event_id FROM events_in_day WHERE day = %s AND user_id = %s",
                                              (dt.timestamp(), authentication.user_id))
        res = cursor.fetchall()
        for row in res:
            event_ids.add(row["event_id"])
        dt += datetime.timedelta(days=1)

    stmt = ""
    for event_id in event_ids:
        stmt += f"SELECT * FROM events WHERE event_id = {event_id};"
    cursor.execute(stmt, multi=True)
    res = cursor.fetchall()
    return {"events": res}


@router.put("/api/calendar/events/{event_id}")
def update_calendar_event(authentication: Authentication, event_id: int, event: CalendarEvent):
    res = get_calendar_event(authentication, event_id)
    time_changed = False
    if res["start_instant"] != event.startInstant or res["end_instant"] != event.endInstant:
        time_changed = True
    cursor.execute("UPDATE events SET %s = %s, %s = %s, %s = %s, %s = %s, %s = %s, %s = %s, %s = %s, %s = %s WHERE event_id = %s",
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
        cursor.execute("DELETE FROM events_in_day WHERE event_id = %s", (event_id,))
        query, params = event.get_sql_events_in_day_insert_query_and_params()
        cursor.execute(query, params)  # add back to events_in_day

    # yuhhhhhh


@router.delete("/api/calendar/events/{event_id}")
def delete_event(authentication: Authentication, event_id: int):
    get_calendar_event(authentication, event_id)  # authenticate
    cursor.execute("DELETE FROM events WHERE event_id = %s", (event_id,))
    cursor.execute("DELETE FROM events_in_day WHERE event_id = %s", (event_id,))
    return f"successfully deleted event with id: '{event_id}'"


@router.delete("/api/calendar/events")
def delete_events_of_user(authentication: Authentication):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    cursor.execute("DELETE FROM events WHERE user_id = %s", (authentication.user_id,))
    cursor.execute("DELETE FROM events_in_day WHERE user_id = %s", (authentication.user_id,))
