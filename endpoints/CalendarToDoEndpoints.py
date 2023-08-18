import datetime
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
import mysql
from mysql.connector.cursor import MySQLCursor, Error
from models.ToDo import ToDo
from models.Authentication import Authentication
from models.SQLColumnNames import *
from endpoints import UserEndpoints, RecurrenceEndpoints, GoalAchievingEndpoints

# TODO: make sure IN ALL ENDPOINTS when a user creates a resource the user_id matches

MEASURING_UNIT_CHAR_LIMIT = 12
router = APIRouter()
cursor: MySQLCursor


@router.post("/api/calendar/todos")
def create_todo(authentication: Authentication, todo: ToDo):
    user_id = authentication.user_id
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    __validate_todo(authentication, todo)
    cursor.execute(
        todo.get_sql_insert_query(),
        todo.get_sql_insert_params())

    # insert into todos_by_user_day
    todo.todoId = cursor.lastrowid
    if todo.endInstant is None:
        cursor.execute("INSERT INTO todos_without_deadline (todo_id, user_id) VALUES %s, %s;", (todo.todoId, todo.userId))
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
    return {"todo": ToDo.from_sql_res(res.__dict__)}

@router.get("/api/calendar/todos")
def get_todos(authentication: Authentication, days: list[float]):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    if len(days) == 0:
        raise HTTPException(detail="Must provide get_todos() with list of days to retrieve", status_code=400)
    year_months = set()
    for day in days:
        dt = datetime.fromtimestamp(day)
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        day = dt.timestamp()
        year_months.add((dt.year, dt.month))

    for year, month in year_months:
        # register what months we are accessing to generate recurrence todos
        RecurrenceEndpoints.register_month_accessed_by_user(authentication, year, month)

    todos_by_day = {}
    cursor.execute("SELECT * FROM todos WHERE todo_id IN"
                   "(SELECT todo_id FROM todos_without_deadline WHERE user_id = %s)", (authentication.user_id,))
    todos_without_deadline = cursor.fetchall()
    for day in days:
        cursor.execute("SELECT * FROM todos WHERE todo_id IN"
                       "(SELECT todo_id FROM todos_in_day WHERE user_id = %s AND day = %s)",
                       (authentication.user_id, day))
        todos_by_day[day] = []
        for row in cursor.fetchall():
            todos_by_day[day].append(ToDo.from_sql_res(row.__dict__))
        for todo_without_deadline in todos_without_deadline:
            todos_by_day[day].append(ToDo.from_sql_res(todo_without_deadline.__dict__))
    return {"todos": todos_by_day}
    # todo: check if lazy loading is implemented here / if it would be faster if we fetched results outside of these loops


@router.get("/api/calendar/todos")
def get_todos(authentication: Authentication, start_day: float, end_day: Optional[float] = None):
    # authenticates in later call to get_todos(Authentication, list[float])
    dt = datetime.fromtimestamp(start_day)
    if end_day is None:
        end_day = start_day
    elif end_day < start_day:
        raise HTTPException(detail="start_day paramater must be less or equal to end_day parameter",
                            status_code=400)
    days = []
    while dt.timestamp() <= end_day:
        dt.replace(hour=0, minute=0, second=0, microsecond=0)
        days.append(dt.timestamp())
        dt += datetime.timedelta(days=1)

    return get_todos(authentication, days)


@router.put("/api/calendar/todos/{todo_id}")
def update_calendar_todo(authentication: Authentication, todo_id: int, updated_todo: ToDo):
    todo = get_todo(authentication, todo_id)["todo"]
    __validate_todo(authentication, todo)
    cursor.execute(
        "UPDATE todos SET %s = %s, %s = %s, %s = %s, %s = %s WHERE todo_id = %s",
        (NAME, updated_todo.name,
         START_INSTANT, updated_todo.startInstant,
         END_INSTANT, updated_todo.endInstant,
         LINKED_GOAL_ID, updated_todo.linkedGoalId,
         todo_id))
    if todo.startInstant != updated_todo.startInstant or todo.endInstant != updated_todo.endInstant:
        cursor.execute("DELETE FROM todos_in_day WHERE todo_id = %s", (todo_id,))
        query, params = updated_todo.get_sql_todos_in_day_insert_query_and_params()
        cursor.execute(query, params)  # add back to todos_in_day


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


def __validate_todo(authentication: Authentication, todo: ToDo):
    if todo.userId is None:
        raise HTTPException(detail="todo missing userId", status_code=400)
    if authentication.user_id != todo.userId:
        raise HTTPException(detail="User is not authenticated to create this resource", status_code=401)
    if todo.name is None:
        raise HTTPException(detail="todo missing a name", status_code=400)
    elif len(todo.name) == 0:
        raise HTTPException(detail="todo missing a name", status_code=400)
    elif len(todo.name) > 32:
        raise HTTPException(detail="todo name must not exceed 32 characters", status_code=400)
    if todo.startInstant is None:
        raise HTTPException(detail="todo missing startInstant", status_code=400)
    if todo.endInstant is not None:
        if todo.endInstant < todo.startInstant:
            raise HTTPException(detail="todo has an invalid endInstant", status_code=400)
    if (todo.recurrenceId is not None and todo.recurrenceDay is None) or \
            (todo.recurrenceId is None and todo.recurrenceDay is not None):
        raise HTTPException(detail="recurrenceId and recurrenceDay must either both be defined, or neither defined",
                            status_code=400)
    # check authentication on goalId
    if todo.linkedGoalId is not None:
        GoalAchievingEndpoints.get_goal(authentication, todo.linkedGoalId)
    # check authentication on recurrenceId
    if todo.recurrenceId is not None:
        RecurrenceEndpoints.get_recurrence(authentication, todo.recurrenceId)
