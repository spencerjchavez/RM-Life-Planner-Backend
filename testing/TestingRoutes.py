from fastapi import APIRouter
from mysql.connector.connection import MySQLCursor
'''
try:
    db_connection = mysql.connector.connect(
        host='154.56.47.154',
        database='u679652356_rm_lp_db_test',
        user='u679652356_admin',
        password='&OQT+W!?3mEh:2[0imK6a',
        autocommit=True
    )
    cursor = db_connection.cursor(dictionary=True)
    if db_connection.is_connected():
        print('Connected to database')
except Error as e:
    print(f'Error connecting to MySQL database: {e}')
'''

router = APIRouter()
cursor: MySQLCursor


@router.post("/api/testing/reset_tables")
def reset_tables():
    with open("testing/init_tables_script.sql", 'r') as file:
        script = file.read()
        file.close()
        for _ in cursor.execute(script, multi=True):
            pass
        _ = cursor.fetchall()
        print("successfully reset tables")
        return
