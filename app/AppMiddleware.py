import asyncio
from asyncio.exceptions import TimeoutError
from urllib.request import Request

from starlette.middleware.base import BaseHTTPMiddleware
from mysql.connector import OperationalError

TIMEOUT = 90


class AppMiddleware(BaseHTTPMiddleware):

    """
    users_pool: MySQLConnectionPool
    todos_pool: MySQLConnectionPool
    events_pool: MySQLConnectionPool
    goals_pool: MySQLConnectionPool
    desires_pool: MySQLConnectionPool
    recurrences_pool: MySQLConnectionPool
    """
    async def dispatch(self, request: Request, call_next):
        try:
            return await self.make_call_with_timeout(request, call_next)
        except OperationalError as e:
            print("lost connection to MySQL database during operation, attempting to recover...")
            print(e)
            return await self.make_call_with_timeout(request, call_next)

    async def make_call_with_timeout(self, request: Request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=TIMEOUT)
        except TimeoutError as e:
            print("Received timeout error with the following request params!")
            print(request.__dict__)
            raise e

