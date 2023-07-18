import datetime
import json
from datetime import datetime
from typing import Optional

import fastapi
from fastapi import APIRouter, HTTPException
from mysql.connector.cursor import MySQLCursor
from models.ToDo import ToDo
from endpoints import UserEndpoints
from models.Authentication import Authentication
from endpoints.MonthsAccessedByUserEndpoints import MonthsAccessedByUser
from models.SQLColumnNames import SQLColumnNames as _


class CalendarToDoEndpoints:
    # TODO: make sure IN ALL ENDPOINTS when a user creates a resource the user_id matches

    router = APIRouter()
    cursor: MySQLCursor

    @staticmethod
    @router.post("/api/calendar/todos")
    def create_todo(authentication: Authentication, todo: ToDo):
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)

        CalendarToDoEndpoints.cursor.execute(
            todo.get_sql_insert_query(),
            todo.get_sql_insert_params())

        # insert into todos_by_user_day
        stmt, params = todo.get_sql_todos_in_day_insert_query_and_params()
        CalendarToDoEndpoints.cursor.execute(stmt, params)
        return {"message": "todo successfully added", "todo_id": todo.todoId}, 200

    @staticmethod
    @router.get("/api/calendar/todos")
    def get_todo(authentication: Authentication, todo_id: int):
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        CalendarToDoEndpoints.cursor.execute("SELECT * FROM todos WHERE todo_id = %s", (todo_id,))
        res = CalendarToDoEndpoints.cursor.fetchone()
        if res["user_id"] != authentication.user_id:
            raise HTTPException(detail="User is not authenticated to access this resource", status_code=401)
        return res, 200

    @staticmethod
    @router.get("/api/calendar/todos")
    def get_todos(authentication: Authentication, start_day: float, end_day: Optional[float] = None):
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        dt = datetime.fromtimestamp(start_day)
        todo_ids = set()
        if end_day is None:
            end_day = start_day
        while dt.timestamp() <= end_day:
            dt.replace(hour=0, minute=0, second=0, microsecond=0)
            year = dt.year
            month = dt.month
            # register that we are accessing month to generate recurrence todos
            MonthsAccessedByUser.register_month_accessed_by_user(authentication, year, month)
            CalendarToDoEndpoints.cursor.execute("SELECT todo_id FROM todos_in_day WHERE day = %s AND user_id = %s",
                                                 (dt.timestamp(), authentication.user_id))
            res = CalendarToDoEndpoints.cursor.fetchall()
            for row in res:
                todo_ids.add(row["todo_id"])
            dt += datetime.timedelta(days=1)

        stmt = ""
        for todo_id in todo_ids:
            stmt += f"SELECT * FROM todos WHERE todo_id = {todo_id};"
        CalendarToDoEndpoints.cursor.execute(stmt, multi=True)
        res = CalendarToDoEndpoints.cursor.fetchall()
        return {"todos": res}, 200

    @staticmethod
    @router.put("/api/calendar/todos/{todo_id}")
    def update_calendar_todo(authentication: Authentication, todo_id: int, todo: ToDo):
        res = CalendarToDoEndpoints.get_todo(authentication, todo_id)
        time_changed = False
        if res["start_instant"] != todo.startInstant or res[_.TIMEFRAME] != todo.timeframe:
            time_changed = True
        CalendarToDoEndpoints.cursor.execute(
            "UPDATE todos SET %s = %s, %s = %s, %s = %s, %s = %s WHERE todo_id = %s",
            (_.NAME, todo.name,
             _.START_INSTANT, todo.startInstant,
             _.TIMEFRAME, todo.timeframe,
             _.LINKED_GOAL_ID, todo.linkedGoalId,
             todo_id))
        if time_changed:
            CalendarToDoEndpoints.cursor.execute("DELETE FROM todos_in_day WHERE todo_id = %s", (todo_id,))
            query, params = todo.get_sql_todos_in_day_insert_query_and_params()
            CalendarToDoEndpoints.cursor.execute(query, params)  # add back to todos_in_day

        # yuhhhhhh
        return 200

    @staticmethod
    @router.delete("/api/calendar/todos/{todo_id}")
    def delete_todo(authentication: Authentication, todo_id: int):
        CalendarToDoEndpoints.get_todo(authentication, todo_id)  # authenticate
        CalendarToDoEndpoints.cursor.execute("DELETE FROM todos WHERE todo_id = %s", (todo_id,))
        CalendarToDoEndpoints.cursor.execute("DELETE FROM todos_in_day WHERE todo_id = %s", (todo_id,))
        return f"successfully deleted todo with id: '{todo_id}'", 200

    @staticmethod
    @router.delete("/api/calendar/todos")
    def delete_todos_of_user(authentication: Authentication):
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        CalendarToDoEndpoints.cursor.execute("DELETE FROM todos WHERE user_id = %s", (authentication.user_id,))
        CalendarToDoEndpoints.cursor.execute("DELETE FROM todos_in_day WHERE user_id = %s", (authentication.user_id,))
