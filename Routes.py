# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

import uvicorn
from fastapi import FastAPI
from endpoints.GoalAchievingEndpoints import GoalAchievingEndpoints
from endpoints.RecurrenceEndpoints import RecurrenceEndpoints
from endpoints.AlertEndpoints import AlertEndpoints
from endpoints.CalendarToDoEndpoints import CalendarToDoEndpoints
from endpoints.CalendarEventEndpoints import CalendarEventEndpoints
import mysql.connector
from mysql.connector import Error


class Routes:
    def __init__(self):

                alert_endpoints = AlertEndpoints(cursor=cursor)
                recurrence_endpoints = RecurrenceEndpoints(cursor=cursor, user_endpoints=user_endpoints)
                calendar_event_endpoints = CalendarEventEndpoints(cursor=cursor, user_endpoints=user_endpoints, recurrence_endpoints=recurrence_endpoints)
                calendar_todo_endpoints = CalendarToDoEndpoints(cursor=cursor, user_endpoints=user_endpoints, recurrence_endpoints=recurrence_endpoints)
                goal_achieving_endpoints = GoalAchievingEndpoints(cursor=cursor, user_endpoints=user_endpoints)

                app = FastAPI()
                app.include_router(user_endpoints.router)
                app.include_router(alert_endpoints.router)
                app.include_router(calendar_event_endpoints.router)
                app.include_router(calendar_todo_endpoints.router)
                app.include_router(recurrence_endpoints.router)
                app.include_router(goal_achieving_endpoints.router)

                uvicorn.run(app, host="localhost", port=8000)

