# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

import uvicorn
from fastapi import FastAPI
from endpoints import UserEndpoints, AlertEndpoints, CalendarToDoEndpoints, CalendarEventEndpoints, GoalAchievingEndpoints, RecurrenceEndpoints
import mysql.connector
from mysql.connector import Error


class Routes:
    def __init__(self):
        app = FastAPI()
        app.include_router(UserEndpoints.router)
        #app.include_router(AlertEndpoints.router)
        app.include_router(CalendarEventEndpoints.router)
        app.include_router(CalendarToDoEndpoints.router)
        app.include_router(RecurrenceEndpoints.router)
        app.include_router(GoalAchievingEndpoints.router)

        uvicorn.run(app, host="localhost", port=8000)

