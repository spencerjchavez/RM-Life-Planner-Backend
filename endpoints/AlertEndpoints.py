from fastapi import APIRouter, HTTPException
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
        pass

    @staticmethod
    @router.get("/api/alerts/{event_id}")
    def get_alerts(event_id: int):
        pass

    @staticmethod
    @router.put("/api/alerts/{event_id}")
    def update_alerts(event_id: int, times: [float]):
        pass

    @staticmethod
    @router.delete("/api/alerts/{event_id}")
    def delete_alert(event_id: int, time: float):
        pass

    @staticmethod
    @router.delete("/api/alerts/{event_id}")
    def delete_alerts(event_id: int):  # delete all alerts with event_id
        pass