import time

from mysql.connector import ProgrammingError, PoolError
from mysql.connector.pooling import MySQLConnectionPool


class DBConnections:
    db_credentials: dict
    db_connection_pool: MySQLConnectionPool

    @staticmethod
    def init_db_connections():
        print("initializing database connection pools")
        '''
        cannot exceed 25 connections per user on mysql database
        '''
        DBConnections.db_connection_pool = DBConnections.create_db_connection_pool("global_pool", 25)
        #TestingRoutes.db_connection_pool = DBConnections.db_connection_pool
        '''
        AppMiddleware.users_pool = AppMiddleware.create_db_connection_pool("user_pool", 2)
        AppMiddleware.todos_pool = AppMiddleware.create_db_connection_pool("todo_pool", 10)
        AppMiddleware.events_pool = AppMiddleware.create_db_connection_pool("event_pool", 10)
        AppMiddleware.desires_pool = AppMiddleware.create_db_connection_pool("desire_pool", 1)
        AppMiddleware.goals_pool = AppMiddleware.create_db_connection_pool("goal_pool", 5)
        AppMiddleware.recurrences_pool = AppMiddleware.create_db_connection_pool("recurrence_pool", 10)
        '''


    @staticmethod
    def create_db_connection_pool(pool_name: str, pool_size: int):
        try:
            return MySQLConnectionPool(
                pool_name=pool_name,
                pool_size=pool_size,
                autocommit=True,
                **DBConnections.db_credentials
            )
        except ProgrammingError as e:
            print(f'Error connecting to MySQL database: {e}')
            raise e

    @staticmethod
    def init_db_credentials(test_mode: bool):
        PRODUCTION_DB_CREDENTIALS = {
            "host": '62.72.50.52',
            "database": 'u721863814_rm_lp_db1',
            "user": 'u721863814_server',
            "password": '5UP3RDUP3R43cr3tP455W0RD#b3tT3rTh4nY0ulelgG@u2??::'
        }
        TEST_DB_CREDENTIALS = {
            "host": '62.72.50.52',
            "database": 'u721863814_rm_lb_test_db',
            "user": 'u721863814_admin',
            "password": 'gSIhnrQ*&2zSs7[7[ND;$C1@CVQMp>zY'
        }
        DBConnections.db_credentials = TEST_DB_CREDENTIALS if test_mode else PRODUCTION_DB_CREDENTIALS

    @staticmethod
    def get_db_connection():
        for i in range(10):
            try:
                return DBConnections.db_connection_pool.get_connection()
            except PoolError as err:
                time.sleep(.15)
        raise PoolError
