from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Query
import mysql.connector
from mysql.connector import Error

router = APIRouter()


class AlertEndpoints:

    try:
        google_db_connection = mysql.connector.connect(
            host='34.31.57.31',
            database='database1',
            user='root',
            password='supersecretdatabase$$keepout',
            autocommit=True
        )
        connection = google_db_connection
        users_cursor = connection.cursor(dictionary=True)
        if connection.is_connected():
            print('Connected to users database')
    except Error as e:
        print(f'Error connecting to MySQL database: {e}')

    @staticmethod
    @router.post("/api/alerts")
    def create_alert(event_id: int, when: float):
        return 200

    @staticmethod
    @router.get("/api/alerts/{event_id}")
    def get_alerts(event_id: int):
        return 200

    @staticmethod
    @router.put("/api/alerts/{event_id}")
    def update_alerts(event_id: int, times: Annotated[Optional[list[float]], Query()]):
        return 200

    @staticmethod
    @router.delete("/api/alerts/{event_id}")
    def delete_alert(event_id: int, time: float):
        return 200

    @staticmethod
    @router.delete("/api/alerts/{event_id}")
    def delete_alerts(event_id: int):  # delete all alerts with event_id
        return 200
