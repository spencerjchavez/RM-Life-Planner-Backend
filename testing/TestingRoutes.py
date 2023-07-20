from fastapi import APIRouter
from mysql.connector.cursor import MySQLCursor
import mysql
from mysql.connector.connection import MySQLCursor, Error

router = APIRouter()

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


@router.post("/api/testing/reset_tables")
def reset_tables():
    with open("testing/init_tables_script.sql", 'r') as file:
        script = file.read()
        file.close()
        for _ in cursor.execute(script, multi=True):
            pass
        print("successfully reset tables")
        return
