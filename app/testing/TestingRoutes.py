from fastapi import APIRouter
from app.db_connections import DBConnections
from app.endpoints import RecurrenceEndpoints

router = APIRouter()


@router.post("/api/testing/reset_tables")
def reset_tables():
    conn = DBConnections.get_db_connection()
    cursor = conn.cursor()
    try:
        with open("testing/init_tables_script.sql", 'r') as file:
            script = file.read()
            file.close()
            for _ in cursor.execute(script, multi=True):
                pass
            _ = cursor.fetchall()
            RecurrenceEndpoints.months_accessed_cache = {}
            return
    finally:
        conn.close()
