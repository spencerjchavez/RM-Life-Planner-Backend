from models.ToDo import ToDo
from fastapi import APIRouter, HTTPException
import mysql.connector.cursor
from endpoints import UserEndpoints
from models.Authentication import Authentication


class CalendarToDoEndpoints:

    router = APIRouter()
    cursor: mysql.connector.cursor
    @staticmethod
    @router
    def create_todo(authentication: Authentication, todo: ToDo):
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)

        # insert into todo_by_user_todo_id
        if todo.userId != user_id:
            raise HTTPException(status_code=401, detail="user not authorized to access this element")
        todo_id = CalendarEventEndpoints.get_next_todo_id(user_id)
        key_id = CalendarEventEndpoints.combine_unsigned_ints_bytes(user_id, todo_id)
        columns = "key_id, name, end_instant, start_day, recurrence_id, goal_id, plan_id, action_id"
        CalendarEventEndpoints.cursor.execute(
            "INSERT INTO todos_by_user_todo_id (%s) values (%s, %s, %s, %s, %s, %s, %s, %s)", (columns,
                                                                                               key_id, todo.name,
                                                                                               todo.endInstant,
                                                                                               todo.startDay,
                                                                                               todo.recurrenceId,
                                                                                               todo.goalId,
                                                                                               todo.planId,
                                                                                               todo.actionId))

        # insert into todo_by_user_day
        days = []
        CalendarEventEndpoints