import datetime
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
import mysql
from mysql.connector.cursor import MySQLCursor, Error
from models.ToDo import ToDo
from models.Authentication import Authentication
from models.SQLColumnNames import *
from endpoints import UserEndpoints, RecurrenceEndpoints

# TODO: make sure IN ALL ENDPOINTS when a user creates a resource the user_id matches

MEASURING_UNIT_CHAR_LIMIT = 12
router = APIRouter()
cursor: MySQLCursor


@router.post("/api/calendar/todos")
def create_todo(authentication: Authentication, todo: ToDo):
    user_id = authentication.user_id
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)

    cursor.execute(
        todo.get_sql_insert_query(),
        todo.get_sql_insert_params())

    # insert into todos_by_user_day
    if todo.deadline is None:
        cursor.execute()
    else:
        stmt, params = todo.get_sql_todos_in_day_insert_query_and_params()
        cursor.execute(stmt, params)
    return {"message": "todo successfully added", "todo_id": todo.todoId}


@router.get("/api/calendar/todos")
def get_todo(authentication: Authentication, todo_id: int):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    cursor.execute("SELECT * FROM todos WHERE todo_id = %s", (todo_id,))
    res = cursor.fetchone()
    if res["user_id"] != authentication.user_id:
        raise HTTPException(detail="User is not authenticated to access this resource", status_code=401)
    return res


@router.get("/api/calendar/todos")
def get_todos(authentication: Authentication, days: list[float]):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    year_months = set()
    for day in days:
        dt = datetime.fromtimestamp(day)
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        day = dt.timestamp()
        year_months.add((dt.year, dt.month))

    for year, month in year_months:
        # register what months we are accessing to generate recurrence events
        RecurrenceEndpoints.register_month_accessed_by_user(authentication, year, month)


    todos_by_day = {}
    cursor.execute("SELECT * FROM todos WHERE todo_id IN"
                   "(SELECT todo_id FROM todos_without_deadline WHERE user_id = %s)", (authentication.user_id,))
    todos_without_deadline = cursor.fetchall()
    for day in days:
        cursor.execute("SELECT * FROM events WHERE event_id IN"
                       "(SELECT event_id FROM events_in_day WHERE user_id = %s AND day = %s)",
                       (authentication.user_id, day))
        todos_by_day[day] = []
        for row in cursor.fetchall():
            todos_by_day[day].append(ToDo.from_sql_res(row.__dict__))
        for todo_without_deadline in todos_without_deadline:
            todos_by_day[day].append(todo_without_deadline.__dict__)
    return {"todos": todos_by_day}
    # todo: check if lazy loading is implemented here / if it would be faster if we fetched results outside of these loops


@router.get("/api/calendar/todos")
def get_todos(authentication: Authentication, start_day: float, end_day: Optional[float] = None):
    # authenticates in later call to get_todos(Authentication, list[float])
    dt = datetime.fromtimestamp(start_day)
    if end_day is None:
        end_day = start_day
    days = []
    while dt.timestamp() <= end_day:
        dt.replace(hour=0, minute=0, second=0, microsecond=0)
        days.append(dt.timestamp())
        dt += datetime.timedelta(days=1)

    return get_todos(authentication, days)


@router.put("/api/calendar/todos/{todo_id}")
def update_calendar_todo(authentication: Authentication, todo_id: int, updated_todo: ToDo):
    res = get_todo(authentication, todo_id)
    time_changed = False
    if res["start_instant"] != todo.startInstant or res[TIMEFRAME] != todo.timeframe:
        time_changed = True
    cursor.execute(
        "UPDATE todos SET %s = %s, %s = %s, %s = %s, %s = %s WHERE todo_id = %s",
        (NAME, updated_todo.name,
         START_INSTANT, updated_todo.startInstant,
         END_INSTANT, updated_todo.endInstant,
         LINKED_GOAL_ID, updated_todo.linkedGoalId,
         todo_id))
    if time_changed:
        cursor.execute("DELETE FROM todos_in_day WHERE todo_id = %s", (todo_id,))
        query, params = updated_todo.get_sql_todos_in_day_insert_query_and_params()
        cursor.execute(query, params)  # add back to todos_in_day
    # yuhhhhhh


@router.delete("/api/calendar/todos/{todo_id}")
def delete_todo(authentication: Authentication, todo_id: int):
    get_todo(authentication, todo_id)  # authenticate
    cursor.execute("DELETE FROM todos WHERE todo_id = %s", (todo_id,))
    cursor.execute("DELETE FROM todos_in_day WHERE todo_id = %s", (todo_id,))
    return f"successfully deleted todo with id: '{todo_id}'"


@router.delete("/api/calendar/todos")
def delete_todos_of_user(authentication: Authentication):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    cursor.execute("DELETE FROM todos WHERE user_id = %s", (authentication.user_id,))
    cursor.execute("DELETE FROM todos_in_day WHERE user_id = %s", (authentication.user_id,))
