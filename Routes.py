# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

import uvicorn
from fastapi import FastAPI, HTTPException
from starlette.requests import Request

from AppMiddleware import AppMiddleware
from endpoints import UserEndpoints, AlertEndpoints, CalendarToDoEndpoints, CalendarEventEndpoints, GoalAchievingEndpoints, RecurrenceEndpoints
from testing import TestingRoutes
import mysql.connector
from mysql.connector import Error, MySQLConnection


class Routes:

    def __init__(self):

        app = FastAPI()
        AppMiddleware.init_db_connection()
        app.add_middleware(AppMiddleware)
        app.include_router(UserEndpoints.router)
        app.include_router(AlertEndpoints.router)
        app.include_router(CalendarEventEndpoints.router)
        app.include_router(CalendarToDoEndpoints.router)
        app.include_router(RecurrenceEndpoints.router)
        app.include_router(GoalAchievingEndpoints.router)
        app.include_router(TestingRoutes.router)

        uvicorn.run(app, host="localhost", port=8000)

        @app.exception_handler(TimeoutError)
        async def timeout_exception_handler(request: Request, exc: TimeoutError):
            print("Received timeout error with the following request params!")
            print(request)
            raise HTTPException(detail="Request timed out", status_code=500)
