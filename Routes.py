# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

import uvicorn
from fastapi import FastAPI
from endpoints.UserEndpoints import UserEndpoints
from endpoints.GoalAchievingEndpoints import GoalAchievingEndpoint
from endpoints.RecurrenceEndpoints import RecurrenceEndpoints
from endpoints.AlertEndpoints import AlertEndpoints
from endpoints.CalendarToDoEndpoints import CalendarToDoEndpoints
from endpoints.CalendarEventEndpoints import CalendarEventEndpoints
from endpoints.MonthsAccessedByUserEndpoints import HelperFunctions
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
            if db_connection.is_connected():
                print('Connected to database')

                UserEndpoints.cursor = cursor
                AlertEndpoints.cursor = cursor
                CalendarToDoEndpoints.cursor = cursor
                CalendarEventEndpoints.cursor = cursor
                RecurrenceEndpoints.cursor = cursor
                GoalAchievingEndpoint.cursor = cursor
                HelperFunctions.cursor = cursor

                app = FastAPI()
                app.include_router(UserEndpoints.router)
                app.include_router(AlertEndpoints.router)
                app.include_router(CalendarEventEndpoints.router)
                app.include_router(CalendarToDoEndpoints.router)
                app.include_router(RecurrenceEndpoints.router)
                app.include_router(GoalAchievingEndpoint.router)

                uvicorn.run(app, host="localhost", port=8000)

        except Error as e:
            print(f'Error connecting to MySQL database: {e}')