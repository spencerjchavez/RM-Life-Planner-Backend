# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

import uvicorn
from fastapi import FastAPI
from endpoints import UserEndpoints, AlertEndpoints, CalendarToDoEndpoints, CalendarEventEndpoints, GoalAchievingEndpoints, RecurrenceEndpoints
from testing import TestingRoutes
import mysql.connector
from mysql.connector import Error


class Routes:
    def __init__(self):

        try:
            db_connection = mysql.connector.connect(
                host='34.31.57.31',
                database='database1',
                user='root',
                password='supersecretdatabase$$keepout',
                autocommit=True
            )
            cursor = db_connection.cursor(dictionary=True)
            CalendarEventEndpoints.cursor = cursor
            CalendarToDoEndpoints.cursor = cursor
            GoalAchievingEndpoints.cursor = cursor
            RecurrenceEndpoints.cursor = cursor
            UserEndpoints.cursor = cursor
            AlertEndpoints.cursor = cursor
            if db_connection.is_connected():
                print('Connected to database')
        except Error as e:
            print(f'Error connecting to MySQL database: {e}')

        app = FastAPI()
        app.include_router(UserEndpoints.router)
        app.include_router(AlertEndpoints.router)
        app.include_router(CalendarEventEndpoints.router)
        app.include_router(CalendarToDoEndpoints.router)
        app.include_router(RecurrenceEndpoints.router)
        app.include_router(GoalAchievingEndpoints.router)
        app.include_router(TestingRoutes.router)

        uvicorn.run(app, host="localhost", port=8000)

