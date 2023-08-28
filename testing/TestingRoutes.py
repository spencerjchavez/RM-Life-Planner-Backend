from fastapi import APIRouter
from mysql.connector.connection import MySQLCursor
from endpoints import RecurrenceEndpoints

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
        RecurrenceEndpoints.months_accessed_cache = {}
        print("successfully reset tables")
        return
