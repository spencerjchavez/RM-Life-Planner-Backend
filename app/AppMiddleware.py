import asyncio
from asyncio.exceptions import TimeoutError
from urllib.request import Request

import mysql.connector.errors
from starlette.middleware.base import BaseHTTPMiddleware
from mysql.connector import OperationalError, MySQLConnection, Connect

from app.endpoints import AlertEndpoints, GoalAchievingEndpoints, CalendarToDoEndpoints, RecurrenceEndpoints, \
    CalendarEventEndpoints, UserEndpoints

from testing import TestingRoutes

TIMEOUT = 90


class AppMiddleware(BaseHTTPMiddleware):

    db_connection: MySQLConnection

    async def dispatch(self, request: Request, call_next):
        try:
            if not AppMiddleware.db_connection.is_connected():
                print("detected that db is not connected, reconnecting...")
                AppMiddleware.db_connection.close()
                AppMiddleware.init_db_connection()
            return await self.make_call_with_timeout(request, call_next)
        except OperationalError as e:
            print("lost connection to MySQL database during operation, attempting to recover...")
            print(e)
            AppMiddleware.db_connection.close()
            AppMiddleware.init_db_connection()
            return await self.make_call_with_timeout(request, call_next)

    async def make_call_with_timeout(self, request: Request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=TIMEOUT)
        except TimeoutError as e:
            print("Received timeout error with the following request params!")
            print(request.__dict__)
            raise e

    @staticmethod
    def init_db_connection():
        try:
            print("initializing db connection")
            db_connection = Connect(
                host='154.56.47.154',
                database='u679652356_rm_lp_db_test',
                user='u679652356_admin',
                password='&OQT+W!?3mEh:2[0imK6a',
                autocommit=True
            )
            AppMiddleware.db_connection = db_connection
            cursor = db_connection.cursor(dictionary=True)
            CalendarEventEndpoints.cursor = cursor
            CalendarEventEndpoints.db = db_connection
            CalendarToDoEndpoints.cursor = cursor
            CalendarToDoEndpoints.db = db_connection
            GoalAchievingEndpoints.cursor = cursor
            GoalAchievingEndpoints.db = db_connection
            RecurrenceEndpoints.cursor = cursor
            RecurrenceEndpoints.db = db_connection
            UserEndpoints.cursor = cursor
            UserEndpoints.db = db_connection
            AlertEndpoints.cursor = cursor
            AlertEndpoints.db = db_connection
            TestingRoutes.cursor = cursor
            TestingRoutes.db = db_connection
            if db_connection.is_connected():
                print('Connected to database')
            else:
                raise mysql.connector.errors.ProgrammingError
        except mysql.connector.errors.ProgrammingError as e:
            print(f'Error connecting to MySQL database: {e}')
            raise e
