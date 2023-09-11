import asyncio
from asyncio.exceptions import TimeoutError
from urllib.request import Request

import mysql.connector.errors
from starlette.middleware.base import BaseHTTPMiddleware
from mysql.connector import OperationalError, Connect

TIMEOUT = 90


class AppMiddleware(BaseHTTPMiddleware):

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
            db_connection = AppMiddleware.get_db_connection()
            return await self.make_call_with_timeout(request, call_next, **{"cursor": db_connection.cursor(dictionary=True)})
        except OperationalError as e:
            print("lost connection to MySQL database during operation, attempting to recover...")
            print(e)
            if db_connection is not None:
                db_connection.close()
            db_connection = AppMiddleware.get_db_connection()
            return await self.make_call_with_timeout(request, call_next, **{"cursor": db_connection.cursor(dictionary=True)})

    async def make_call_with_timeout(self, request: Request, call_next, **kwargs):
        try:
            return await asyncio.wait_for(call_next(request, **kwargs), timeout=TIMEOUT)
        except TimeoutError as e:
            print("Received timeout error with the following request params!")
            print(request.__dict__)
            raise e

    @staticmethod
    def get_db_connection():
        try:
            print("getting db connection")
            db_connection = Connect(
                host=AppMiddleware.host,
                database=AppMiddleware.database_name,
                user=AppMiddleware.user,
                password=AppMiddleware.password,
                autocommit=True
            )
            if db_connection.is_connected():
                print('Connected to database')
                return db_connection
            else:
                raise mysql.connector.errors.ProgrammingError
        except mysql.connector.errors.ProgrammingError as e:
            print(f'Error connecting to MySQL database: {e}')
            raise e
