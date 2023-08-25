import asyncio
from asyncio.exceptions import TimeoutError
from aifc import Error
from asyncio import CancelledError
from urllib.request import Request

import mysql
from mysql.connector import OperationalError, MySQLConnection, ProgrammingError
from endpoints import UserEndpoints, AlertEndpoints, CalendarToDoEndpoints, CalendarEventEndpoints, GoalAchievingEndpoints, RecurrenceEndpoints
from starlette.middleware.base import BaseHTTPMiddleware

from testing import TestingRoutes

TIMEOUT = 15

class AppMiddleware(BaseHTTPMiddleware):

    db_connection: MySQLConnection

    async def dispatch(self, request: Request, call_next):
        try:
            return await self.make_call_with_timeout(request, call_next)
        except OperationalError:
            print("Operational Error: lost connection to SQL DB, attempting to reconnect!")
            AppMiddleware.db_connection.close()
            AppMiddleware.init_db_connection()
            return await self.make_call_with_timeout(request, call_next)
        except ProgrammingError as e:
            print("ProgrammingError!")
            print(e)
            raise e
            #print("Programming Error: lost connection to SQL DB, attempting to reconnect!")
            #AppMiddleware.db_connection.close()
            #AppMiddleware.init_db_connection()
            return await self.make_call_with_timeout(request, call_next)

    async def make_call_with_timeout(self, request: Request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=TIMEOUT)
        except TimeoutError:
            print("Received timeout error with the following request params!")
            print(request.__dict__)

    @staticmethod
    def init_db_connection():
        try:
            db_connection = mysql.connector.connect(
                host='154.56.47.154',
                database='u679652356_rm_lp_db_test',
                user='u679652356_admin',
                password='&OQT+W!?3mEh:2[0imK6a',
                autocommit=True
            )
            AppMiddleware.db_connection = db_connection
            cursor = db_connection.cursor(dictionary=True)
            CalendarEventEndpoints.cursor = cursor
            CalendarToDoEndpoints.cursor = cursor
            GoalAchievingEndpoints.cursor = cursor
            RecurrenceEndpoints.cursor = cursor
            UserEndpoints.cursor = cursor
            AlertEndpoints.cursor = cursor
            TestingRoutes.cursor = cursor
            if db_connection.is_connected():
                print('Connected to database')
        except Error as e:
            print(f'Error connecting to MySQL database: {e}')
            raise e
