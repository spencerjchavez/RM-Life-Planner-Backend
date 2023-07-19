from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Query
from mysql.connector.cursor import MySQLCursor


class AlertEndpoints:

    router = APIRouter()
    cursor: MySQLCursor

    def __init__(self, cursor: MySQLCursor):
        self.cursor = cursor

    @router.post("/api/alerts")
    def create_alert(self, event_id: int, when: float):
        return 200

    @router.get("/api/alerts/{event_id}")
    def get_alerts(self, event_id: int):
        return 200

    @router.put("/api/alerts/{event_id}")
    def update_alerts(self, event_id: int, times: Annotated[Optional[list[float]], Query()]):
        return 200

    @router.delete("/api/alerts/{event_id}")
    def delete_alert(self, event_id: int, time: float):
        return 200

    @router.delete("/api/alerts/{event_id}")
    def delete_alerts(self, event_id: int):  # delete all alerts with event_id
        return 200
