import datetime
from typing import Optional

from mysql.connector import MySQLConnection

from app.extras.SQLDateValidator import *
from dateutil import relativedelta
from fastapi import APIRouter, HTTPException
from mysql.connector.cursor_cext import CMySQLCursorDict
from app.models.CalendarEvent import CalendarEvent
from app.models.Authentication import Authentication
from app.extras.SQLColumnNames import *
from app.endpoints import CalendarToDoEndpoints, RecurrenceEndpoints, UserEndpoints, GoalAchievingEndpoints

router = APIRouter()
cursor: CMySQLCursorDict
db: MySQLConnection


@router.post("/api/calendar/events")
def create_calendar_event(authentication: Authentication, event: CalendarEvent):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    __validate_event(authentication, event)
    cursor.execute(
        event.get_sql_events_insert_query(),
        event.get_sql_insert_params())
    event.eventId = cursor.lastrowid
    __update_goal_deadline_after_altering_event(event)
    
    return {"message": "event successfully added", "event_id": event.eventId}


@router.get("/api/calendar/events/by-event-id/{event_id}")
def get_calendar_event(auth_user: int, api_key: str, event_id: int):
    authentication = Authentication(auth_user, api_key)
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
    res = cursor.fetchone()
    if res is None:
        raise HTTPException(detail="specified event does not exist", status_code=404)
    if res["user_id"] != authentication.user_id:
        raise HTTPException(detail="User is not authenticated to access this resource", status_code=401)
    return {"event": CalendarEvent.from_sql_res(res)}


@router.get("/api/calendar/events/in-date-list")
def get_calendar_events_by_date_list(auth_user: int, api_key: str, dates: list[str]):
    authentication = Authentication(auth_user, api_key)
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    if len(dates) == 0:
        raise HTTPException(detail="get_calendar_events_by_date_list requires a list of dates to return events for", status_code=400)
    in_clause = ""
    year_months = set()
    for date_str in dates:
        if not validate_date(date_str):
            raise HTTPException(detail="invalid date provided!", status_code=400)
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        year_months.add((dt.year, dt.month))

    for year, month in year_months:
        # register what months we are accessing to generate recurrence events
        RecurrenceEndpoints.register_month_accessed_by_user(authentication, year, month)

    events_by_day = {}
    for date_str in dates:
        cursor.execute("SELECT * FROM events WHERE user_id = %s AND start_day <= %s AND end_day >= %s", (authentication.user_id, date_str, date_str))
        for row in cursor.fetchall():
            events_by_day.setdefault(date_str, []).append(CalendarEvent.from_sql_res(row))
    return {"events": events_by_day}


@router.get("/api/calendar/events/in-date-range")
def get_calendar_events_by_date_range(auth_user: int, api_key: str, start_date: str,
                                      end_date: Optional[str] = None):
    authentication = Authentication(auth_user, api_key)
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    if end_date is None:
        end_date = start_date
    if not validate_date(start_date) or not validate_date(end_date):
        raise HTTPException(detail="invalid date provided!", status_code=400)
    dt = datetime.strptime(start_date, "%Y-%m-%d")
    dt_end = datetime.strptime(end_date, "%Y-%m-%d")
    if dt_end < dt:
        raise HTTPException(detail="end date cannot be before start date!", status_code=400)
    year_months = set()
    while dt <= dt_end:
        year_months.add((dt.year, dt.month))
        dt += relativedelta.relativedelta(months=1)

    for year, month in year_months:
        # register what months we are accessing to generate recurrence events
        RecurrenceEndpoints.register_month_accessed_by_user(authentication, year, month)

    cursor.execute("SELECT * FROM events WHERE user_id = %s AND end_date >= %s AND start_date <= %s",
                   (authentication.user_id, start_date, end_date))
    res = cursor.fetchall()
    events = []
    for row in res:
        events.append(CalendarEvent.from_sql_res(row))
    return {"events": events}


@router.get("/api/calendar/events/by-goal-id/{goal_id}")
def get_calendar_events_by_goal_id(auth_user: int, api_key: str, goal_id: int):
    GoalAchievingEndpoints.get_goal(auth_user, api_key, goal_id)
    cursor.execute("SELECT * FROM events WHERE linked_goal_id = %s", (goal_id,))
    res = cursor.fetchall()
    events = []
    for row in res:
        events.append(CalendarEvent.from_sql_res(row))
    return {"events": events}


@router.post("/api/calendar/events/by-goal-id")
def get_calendar_events_by_goal_ids(auth_user: int, api_key: str, goal_ids: list[int]):
    _ = GoalAchievingEndpoints.get_goals(auth_user, api_key, goal_ids)
    to_return = {}
    in_clause = "("
    in_params = ()
    for goal_id in goal_ids:
        in_clause += "%s,"
        in_params += (goal_id,)
    in_clause = in_clause[:len(in_clause) - 1] + ")"
    cursor.execute("SELECT * FROM events WHERE linked_goal_id IN " + in_clause, in_params)
    res = cursor.fetchall()
    for row in res:
        to_return.setdefault(row["linked_goal_id"], []).append(CalendarEvent.from_sql_res(row))
    return {"events": to_return}


@router.put("/api/calendar/events/{event_id}")
def update_calendar_event(authentication: Authentication, event_id: int, updated_event: CalendarEvent):
    original_event = get_calendar_event(authentication.user_id, authentication.api_key, event_id)["event"]
    updated_event.eventId = event_id
    __validate_event(authentication, updated_event)
    cursor.execute(f"UPDATE events SET {NAME} = %s, {DESCRIPTION} = %s, {IS_HIDDEN} = %s, {START_DATE} = %s, {START_TIME} = %s, {END_DATE} = %s, {END_TIME} = %s, {LINKED_TODO_ID} = %s, {HOW_MUCH_ACCOMPLISHED} = %s, {NOTES} = %s WHERE event_id = %s",
        (updated_event.name,
         updated_event.description,
         updated_event.isHidden,
         updated_event.startDate,
         updated_event.startTime,
         updated_event.endDate,
         updated_event.endTime,
         updated_event.linkedTodoId,
         updated_event.howMuchAccomplished,
         updated_event.notes,
         event_id))
    __update_goal_deadline_after_altering_event(updated_event)
    
    return {"message": "success"}

@router.delete("/api/calendar/events/{event_id}")
def delete_event(auth_user: int, api_key: str, event_id: int):
    get_calendar_event(auth_user, api_key, event_id)  # authenticate
    cursor.execute("DELETE FROM events WHERE event_id = %s", (event_id,))
    
    return f"successfully deleted event with id: '{event_id}'"


@router.delete("/api/calendar/events")
def delete_events_of_user(auth_user: int, api_key: str):
    authentication = Authentication(auth_user, api_key)
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    cursor.execute("DELETE FROM events WHERE user_id = %s", (authentication.user_id,))
    


def __update_goal_deadline_after_altering_event(event: CalendarEvent):
    if event.linkedGoalId is None:
        return
    if event.howMuchAccomplished is None or event.howMuchAccomplished <= 0:
        return
    cursor.execute("SELECT how_much FROM goals WHERE goal_id = %s ", (event.linkedGoalId,))
    goal_how_much = cursor.fetchone()['how_much']
    cursor.execute("SELECT how_much_accomplished FROM events WHERE linked_goal_id = %s", (event.linkedGoalId,))
    how_much_accomplished = cursor.fetchone()["how_much_accomplished"]
    if goal_how_much <= how_much_accomplished:
        # goal is fulfilled, if has no deadline, set one
        cursor.execute("SELECT deadline_date FROM goals WHERE goal_id = %s", (event.linkedGoalId,))
        if cursor.fetchone()["deadline_date"] is None:
            cursor.execute("SELECT MAX(end_date) AS new_deadline FROM events WHERE linked_goal_id = %s", (event.linkedGoalId,))
            new_deadline_date = cursor.fetchone()["new_deadline"]
            cursor.execute("UPDATE goals SET deadline_date = %s WHERE goal_id = %s", (new_deadline_date, event.linkedGoalId))
    

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
    if event.startDate is None:
        raise HTTPException(detail="event missing start date", status_code=400)
    if event.startTime is None:
        raise HTTPException(detail="event missing start time", status_code=400)
    if event.endDate is None:
        raise HTTPException(detail="event missing end date", status_code=400)
    if event.endTime is None:
        raise HTTPException(detail="event missing end time", status_code=400)
    try:
        start_dt = datetime.strptime(event.startDate + " " + event.startTime, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(event.endDate + " " + event.endTime, "%Y-%m-%d %H:%M:%S")
        if end_dt < start_dt:
            raise HTTPException(detail="event's end must be after the event's start", status_code=400)
        if event.recurrenceDate is not None:
            _ = datetime.strptime(event.recurrenceDate, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(detail="invalid date and time provided", status_code=400)
    if event.description is not None:
        if len(event.description) > 500:
            raise HTTPException(detail="event description must not exceed 500 characters", status_code=400)
    # check authentication on todoId
    if event.howMuchAccomplished is not None and event.linkedTodoId is None:
        raise HTTPException(detail="event must define a linkedTodoId in order to define the how much accomplished property", status_code=400)
    if event.linkedTodoId is not None:
        todo = CalendarToDoEndpoints.get_todo(authentication.user_id, authentication.api_key, event.linkedTodoId)["todo"]
        if todo.linkedGoalId != event.linkedGoalId:
            raise HTTPException(
                detail="event must define a linked goal id that matches its todo's linked goal id",
                status_code=400)
        if event.howMuchAccomplished is not None:
            if event.howMuchAccomplished <= 0:
                raise HTTPException(detail="how much accomplished attribute must be greater than 0", status_code=400)
    if event.linkedGoalId is not None and event.linkedTodoId is None:
        raise HTTPException(detail="event must define a linked todo id if it defines a linked goal id", status_code=400)
    if event.notes is not None:
        if event.howMuchAccomplished is None:
            raise HTTPException(detail="cannot define notes section without specifying how much was accomplished", status_code=400)
        if len(event.notes) > 300:
            raise HTTPException(detail="plans notes must not exceed 300 characters", status_code=400)
    if (event.recurrenceId is not None and event.recurrenceDate is None) or \
            (event.recurrenceId is None and event.recurrenceDate is not None):
        raise HTTPException(detail="recurrenceId and recurrenceDay must either both be defined, or neither defined",
                            status_code=400)
    # check authentication on recurrenceId
    if event.recurrenceId is not None:
        RecurrenceEndpoints.get_recurrence(authentication.user_id, authentication.api_key, event.recurrenceId)
