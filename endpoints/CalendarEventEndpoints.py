import datetime
from datetime import datetime
from typing import Optional
import mysql
from fastapi import APIRouter, HTTPException
from mysql.connector.cursor import MySQLCursor, Error
from models.CalendarEvent import CalendarEvent
from models.Authentication import Authentication
from models.SQLColumnNames import *
from endpoints import UserEndpoints, RecurrenceEndpoints, CalendarToDoEndpoints, GoalAchievingEndpoints


# TODO: make sure IN ALL ENDPOINTS when a user creates a resource the user_id matches

router = APIRouter()
cursor: MySQLCursor


@router.post("/api/calendar/events")
def create_calendar_event(authentication: Authentication, event: CalendarEvent):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    __validate_event(authentication, event)
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
    return {"event": CalendarEvent.from_sql_res(res.__dict__) }


@router.get("/api/calendar/events")
def get_calendar_events(authentication: Authentication, days: list[float]):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    if len(days) == 0:
        raise HTTPException(detail="get_calendar_events requires a list of days to return events for", status_code=400)
    in_clause = ""
    year_months = set()
    for day in days:
        dt = datetime.fromtimestamp(day)
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        day = dt.timestamp()
        in_clause += str(day) + ","
        year_months.add((dt.year, dt.month))

    for year, month in year_months:
        # register what months we are accessing to generate recurrence events
        RecurrenceEndpoints.register_month_accessed_by_user(authentication, year, month)

    events_by_day = {}
    for day in days:
        cursor.execute("SELECT * FROM events WHERE event_id IN"
                       "(SELECT event_id FROM events_in_day WHERE user_id = %s AND day = %s)",
                       (authentication.user_id, day))
        events_by_day[day] = []
        for row in cursor.fetchall():
            events_by_day[day].append(CalendarEvent.from_sql_res(row.__dict__))
    return {"events": events_by_day}


@router.get("/api/calendar/events")
def get_calendar_events(authentication: Authentication, start_day: float, end_day: Optional[float] = None):
    # authenticates in later call to get_calendar_events(Authentication, list[float])
    if end_day is None:
        end_day = start_day
    elif end_day < start_day:
        raise HTTPException(detail="start_day paramater must be less or equal to end_day parameter",
                            status_code=400)

    dt = datetime.fromtimestamp(start_day)
    days = []
    while dt.timestamp() <= end_day:
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        days.append(dt.timestamp())
        dt += datetime.timedelta(days=1)

    return get_calendar_events(authentication, days)


@router.put("/api/calendar/events/{event_id}")
def update_calendar_event(authentication: Authentication, event_id: int, updated_event: CalendarEvent):
    original_event = get_calendar_event(authentication, event_id)["event"]
    __validate_event(authentication, updated_event)
    cursor.execute("UPDATE events SET %s = %s, %s = %s, %s = %s, %s = %s, %s = %s, %s = %s, %s = %s WHERE event_id = %s",
                                          (NAME, updated_event.name,
                                           DESCRIPTION, updated_event.description,
                                           IS_HIDDEN, updated_event.isHidden,
                                           START_INSTANT, updated_event.startInstant,
                                           END_INSTANT, updated_event.endInstant,
                                           LINKED_GOAL_ID, updated_event.linkedGoalId,
                                           LINKED_TODO_ID, updated_event.linkedTodoId,
                                           event_id))
    if original_event.startInstant != updated_event.startInstant or original_event.endInstant != updated_event.endInstant:
        cursor.execute("DELETE FROM events_in_day WHERE event_id = %s", (event_id,))
        query, params = updated_event.get_sql_events_in_day_insert_query_and_params()
        cursor.execute(query, params)  # add back to events_in_day


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


def __validate_event(authentication: Authentication, event: CalendarEvent):
    if event.userId is None:
        raise HTTPException(detail="event missing userId", status_code=400)
    if authentication.user_id != event.userId:
        raise HTTPException(detail="User is not authenticated to create this resource", status_code=401)
    if event.name is None:
        raise HTTPException(detail="event missing a name", status_code=400)
    elif len(event.name) == 0:
        raise HTTPException(detail="event missing a name", status_code=400)
    elif len(event.name) > 64:
        raise HTTPException(detail="event name must not exceed 64 characters", status_code=400)
    if event.startInstant is None:
        raise HTTPException(detail="event missing startInstant", status_code=400)
    if event.endInstant is None:
        raise HTTPException(detail="event missing endInstant", status_code=400)
    if event.endInstant < event.startInstant:
        raise HTTPException(detail="event has an invalid endInstant", status_code=400)
    if len(event.description) > 500:
        raise HTTPException(detail="event description must not exceed 500 characters", status_code=400)
    if (event.recurrenceId is not None and event.recurrenceDay is None) or \
            (event.recurrenceId is None and event.recurrenceDay is not None):
        raise HTTPException(detail="recurrenceId and recurrenceDay must either both be defined, or neither defined", status_code=400)
    # check authentication on todoId
    if event.linkedTodoId is not None:
        CalendarToDoEndpoints.get_todo(authentication, event.linkedTodoId)
    # check authentication on goalId
    if event.linkedGoalId is not None:
        GoalAchievingEndpoints.get_goal(authentication, event.linkedGoalId)
    # check authentication on recurrenceId
    if event.recurrenceId is not None:
        RecurrenceEndpoints.get_recurrence(authentication, event.recurrenceId)
