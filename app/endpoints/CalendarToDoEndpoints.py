import datetime
from typing import Optional

from mysql.connector import MySQLConnection

from app.extras.SQLDateValidator import *
from dateutil import relativedelta
from fastapi import APIRouter, HTTPException
from mysql.connector.cursor_cext import CMySQLCursorDict

from app.models.ToDo import ToDo
from app.models.Authentication import Authentication
from app.extras.SQLColumnNames import *
from app.endpoints import GoalAchievingEndpoints, RecurrenceEndpoints, UserEndpoints

MEASURING_UNIT_CHAR_LIMIT = 12
router = APIRouter()
cursor: CMySQLCursorDict
db: MySQLConnection


@router.post("/api/calendar/todos")
def create_todo(authentication: Authentication, todo: ToDo):
    user_id = authentication.user_id
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    __validate_todo(authentication, todo)
    cursor.execute(
        todo.get_sql_insert_query(),
        todo.get_sql_insert_params())
    todo.todoId = cursor.lastrowid
    
    return {"message": "todo successfully added", "todo_id": todo.todoId}


@router.get("/api/calendar/todos/by-todo-id/{todo_id}")
def get_todo(auth_user: int, api_key: str, todo_id: int):
    authentication = Authentication(auth_user, api_key)
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    cursor.execute("SELECT * FROM todos WHERE todo_id = %s", (todo_id,))
    res = cursor.fetchone()
    if res is None:
        raise HTTPException(detail="specified todo does not exist", status_code=404)
    if res["user_id"] != authentication.user_id:
        raise HTTPException(detail="User is not authenticated to access this resource", status_code=401)
    return {"todo": ToDo.from_sql_res(res)}


@router.post("/api/calendar/todos/in-date-list")
def get_todos_by_dates_list(auth_user: int, api_key: str, dates: list[str]):
    authentication = Authentication(auth_user, api_key)
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    if len(dates) == 0:
        raise HTTPException(detail="Must provide get_todos() with list of days to retrieve", status_code=400)
    year_months = set()
    for day in dates:
        if not validate_date(day):
            raise HTTPException(detail="invalid date provided!", status_code=400)
        dt = datetime.strptime(day, "%Y-%m-%d")
        year_months.add((dt.year, dt.month))

    for year, month in year_months:
        # register what months we are accessing to generate recurrence todos
        RecurrenceEndpoints.register_month_accessed_by_user(authentication, year, month)

    todos_by_day = {}
    for date_str in dates:
        cursor.execute("SELECT * FROM todos WHERE user_id = %s AND deadline_date >= %s AND start_date <= %s"
                       "UNION "
                       "SELECT * FROM todos WHERE user_id = %s "
                       "AND start_date <= %s "
                       "AND deadline_date IS NULL "
                       "AND how_much_planned <= (SELECT SUM(how_much_accomplished) FROM events WHERE linked_todo_id = todos.todo_id)"
                       "AND (SELECT MAX(end_date) FROM events WHERE linked_todo_id = todos.todo_id) >= %s"
                       "UNION"
                       "SELECT * FROM todos WHERE user_id = %s "
                       "AND start_date <= %s "
                       "AND deadline_date IS NULL "
                       "AND how_much_planned > (SELECT SUM(how_much_accomplished) FROM events WHERE linked_todo_id = todos.todo_id)",
                       (authentication.user_id, date_str, date_str, authentication.user_id, date_str, date_str,
                        authentication.user_id, date_str))
        todos_by_day[date_str] = []
        for row in cursor.fetchall():
            todos_by_day[date_str].append(ToDo.from_sql_res(row))
    return {"todos": todos_by_day}
    # todo: check if it would be faster if we fetched db results outside of these loops


@router.get("/api/calendar/todos/in-date-range")
def get_todos_in_date_range(auth_user: int, api_key: str, start_date: str, end_date: Optional[str] = None):
    authentication = Authentication(auth_user, api_key)
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    if end_date is None:
        end_date = start_date
    if not validate_date(start_date) or not validate_date(end_date):
        raise HTTPException(detail="invalid date provided!", status_code=400)
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    if end_dt < start_dt:
        raise HTTPException(detail="start_day parameter must be less or equal to end_day parameter",
                            status_code=400)
    year_months = []
    dt = start_dt
    while dt <= end_dt:
        year_months.append((dt.year, dt.month))
        dt += relativedelta.relativedelta(months=1)

    cursor.execute("SELECT * FROM todos WHERE user_id = %s AND deadline_date >= %s AND start_date <= %s"
                   "UNION "
                   "(SELECT * FROM todos WHERE user_id = %s "
                   "AND start_date <= %s "
                   "AND deadline_date IS NULL "
                   "AND how_much_planned <= (SELECT SUM(how_much_accomplished) FROM events WHERE linked_todo_id = todos.todo_id)"
                   "AND (SELECT MAX(end_date) FROM events WHERE linked_todo_id = todos.todo_id) >= %s"
                   ") UNION ("
                   "SELECT * FROM todos WHERE user_id = %s "
                   "AND start_date <= %s "
                   "AND deadline_date IS NULL "
                   "AND how_much_planned > (SELECT SUM(how_much_accomplished) FROM events WHERE linked_todo_id = todos.todo_id))",
                   (authentication.user_id, start_date, end_date, authentication.user_id, end_date, start_date,
                    authentication.user_id, end_date))
    todos = []
    res = cursor.fetchall()
    for row in res:
        todos.append(ToDo.from_sql_res(row))
    return {"todos": todos}


@router.get("/api/calendar/todos/by-goal-id/{goal_id}")
def get_todos_by_goal_id(auth_user: int, api_key: str, goal_id: int):
    GoalAchievingEndpoints.get_goal(auth_user, api_key, goal_id)
    cursor.execute("SELECT * FROM todos WHERE linked_goal_id = %s", (goal_id,))
    res = cursor.fetchall()
    todos = []
    for row in res:
        todos.append(ToDo.from_sql_res(row))
    return {"todos": todos}


@router.post("/api/calendar/todos/by-goal-id/")
def get_todos_by_goal_ids(auth_user: int, api_key: str, goal_ids: list[int]):
    authentication = Authentication(auth_user, api_key)
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    in_clause = ""
    for goal_id in goal_ids:
        in_clause += "," + str(goal_id)
    in_clause = "(" + in_clause[1:] + ")"
    cursor.execute("SELECT * FROM todos WHERE linked_goal_id IN %s", (in_clause,))
    res = cursor.fetchall()
    todos_by_goal_id = {}
    for row in res:
        if row["user_id"] != authentication.user_id:
            raise HTTPException(detail="user not authorized to access this resource!", status_code=401)
        todos_by_goal_id.setdefault(row["linked_goal_id"], []).append(ToDo.from_sql_res(row))
    return {"todos": todos_by_goal_id}


'''
@router.get("/api/calendar/todos/active/{user_id}")
def get_active_todos(authentication: Authentication, user_id: int):
    # returns all todos that do not have a completed plan attached to them
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="user is not authenticated, please log in", status_code=401)
    if authentication.user_id != user_id:
        raise HTTPException(detail="user not authorized to access this resource", status_code=401)
    cursor.execute("SELECT * FROM todos WHERE todo_id IN "
                   "(SELECT todo_id FROM active_todos WHERE user_id = %s)", (user_id,))
    res = cursor.fetchall()
    todos = []
    for row in res:
        todos.append(ToDo.from_sql_res(row))
    return {"todos": todos}
'''


@router.put("/api/calendar/todos/{todo_id}")
def update_calendar_todo(authentication: Authentication, todo_id: int, updated_todo: ToDo):
    todo = get_todo(authentication.user_id, authentication.api_key, todo_id)["todo"]
    updated_todo.todoId = todo_id
    __validate_todo(authentication, updated_todo)
    if todo.linkedGoalId != updated_todo.linkedGoalId:  # need to update child events with new goal id
        cursor.execute("UPDATE events SET linked_goal_id = %s WHERE linked_todo_id = %s AND user_id = %s",
                       (updated_todo.linkedGoalId, todo_id, authentication.user_id))

    cursor.execute(
        f"UPDATE todos SET {NAME} = %s, {START_DATE} = %s, {DEADLINE_DATE} = %s, {HOW_MUCH_PLANNED} = %s, {LINKED_GOAL_ID} = %s WHERE todo_id = %s",
        (updated_todo.name,
         updated_todo.startDate,
         updated_todo.deadlineDate,
         updated_todo.howMuchPlanned,
         updated_todo.linkedGoalId,
         todo_id))
    
    return {"message": "success!"}


@router.delete("/api/calendar/todos/{todo_id}")
def delete_todo(auth_user: int, api_key: str, todo_id: int):
    get_todo(auth_user, api_key, todo_id)  # authenticate
    cursor.execute("DELETE FROM todos WHERE todo_id = %s", (todo_id,))
    return f"successfully deleted todo with id: '{todo_id}'"


@router.delete("/api/calendar/todos")
def delete_todos_of_user(auth_user: int, api_key: str):
    authentication = Authentication(auth_user, api_key)
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    cursor.execute("DELETE FROM todos WHERE user_id = %s", (authentication.user_id,))


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
    if todo.startDate is None:
        raise HTTPException(detail="todo missing start date", status_code=400)
    try:
        start_dt = datetime.strptime(todo.startDate, "%Y-%m-%d")
        if todo.deadlineDate is not None:
            deadline_dt = datetime.strptime(todo.deadlineDate, "%Y-%m-%d")
            if deadline_dt < start_dt:
                raise HTTPException(detail="todo's end instant cannot be less than its start instant", status_code=400)
        if todo.recurrenceDate is not None:
            recurrence_date_dt = datetime.strptime(todo.recurrenceDate, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(detail="goal has improper date properties!", status_code=400)
    # check authentication on goalId
    if todo.howMuchPlanned is None:
        raise HTTPException(detail="todo must define how much planned", status_code=400)
    if todo.howMuchPlanned <= 0:
        raise HTTPException(detail="todo must define how much planned > 0", status_code=400)
    if todo.linkedGoalId is not None:
        GoalAchievingEndpoints.get_goal(authentication.user_id, authentication.api_key, todo.linkedGoalId)
          # check authentication on recurrenceId
    if todo.recurrenceId is not None:
        RecurrenceEndpoints.get_recurrence(authentication.user_id, authentication.api_key, todo.recurrenceId)
    if (todo.recurrenceId is not None and todo.recurrenceDate is None) or \
            (todo.recurrenceId is None and todo.recurrenceDate is not None):
        raise HTTPException(detail="recurrenceId and recurrenceDay must either both be defined, or neither defined",
                            status_code=400)
