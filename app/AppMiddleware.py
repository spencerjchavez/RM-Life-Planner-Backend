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
    host: str
    database_name: str
    user: str
    password: str
    test_mode: bool

    @staticmethod
    def init_db_credentials(test_mode: bool):
        PRODUCTION_DB_CREDENTIALS = {
            "host": '62.72.50.52',
            "database_name": 'u721863814_rm_lp_db1',
            "user": 'u721863814_server',
            "password": '5UP3RDUP3R43cr3tP455W0RD#b3tT3rTh4nY0ulelgG@u2??::'
        }
        TEST_DB_CREDENTIALS = {
            "host": '62.72.50.52',
            "database_name": 'u721863814_rm_lb_test_db',
            "user": 'u721863814_admin',
            "password": 'gSIhnrQ*&2zSs7[7[ND;$C1@CVQMp>zY'
        }
        AppMiddleware.test_mode = test_mode
        credentials = TEST_DB_CREDENTIALS if test_mode else PRODUCTION_DB_CREDENTIALS
        AppMiddleware.host = credentials["host"]
        AppMiddleware.database_name = credentials["database_name"]
        AppMiddleware.user = credentials["user"]
        AppMiddleware.password = credentials["password"]

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
                host=AppMiddleware.host,
                database=AppMiddleware.database_name,
                user=AppMiddleware.user,
                password=AppMiddleware.password,
                autocommit=True
            )
            AppMiddleware.db_connection = db_connection
            cursor = db_connection.cursor(dictionary=True)
            # cursor.execute("USE %s;", ('u721863814_rm_lp_test_db' if AppMiddleware.test_mode else 'u721863814_rm_lp_db1',))
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
