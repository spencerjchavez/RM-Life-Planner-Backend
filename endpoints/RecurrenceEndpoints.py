
from fastapi import APIRouter, HTTPException
from models.Recurrence import Recurrence
import mysql.connector
from mysql.connector import Error


class RecurrenceEndpoints:
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

    except Error as e:
        print(f'Error connecting to MySQL database: {e}')

    router = APIRouter()

    @staticmethod
    @router.post("/api/recurrences")
    def create_recurrence(recurrence: Recurrence):
        q = recurrence.get_sql_insert_query()
        RecurrenceEndpoints.cursor.execute(q)
        return RecurrenceEndpoints.cursor.lastrowid

    @staticmethod
    @router.get("/api/recurrences/{recurrence_id}")
    def get_recurrence(recurrence_id: int):
        pass

    @staticmethod
    @router.put("/api/recurrences/{recurrence_id}")
    def update_recurrence(recurrence_id: int, recurrence: Recurrence):
        pass
    @staticmethod
    @router.delete("/api/recurrences/{recurrence_id}")
    def delete_recurrence(recurrence_id: int):
        pass
