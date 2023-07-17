from typing import Optional

from fastapi import APIRouter, HTTPException

from models.Authentication import Authentication
from models.Recurrence import Recurrence
from mysql.connector.connection import MySQLCursor
from endpoints import UserEndpoints
from models.SQLColumnNames import SQLColumnNames as _
from dateutil.rrule import rrulestr
import datetime
from endpoints.MonthsAccessedByUserEndpoints import MonthsAccessedByUser


class RecurrenceEndpoints:

    router = APIRouter()
    cursor: MySQLCursor
    users_generated_recurrences_map: {int: {int: {int: bool}}}  # user_id, month, year, and if there have been recurrences registered for that month

# TODO: VALIDATE INPUT FOR RECURRENCE OBJECTS

    @staticmethod
    @router.post("/api/recurrences")
    def create_recurrence(authentication: Authentication, recurrence: Recurrence):
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        if recurrence.userId != authentication.user_id:
            raise HTTPException(status_code=401, detail="User is not authenticated to create this resource")
        if recurrence.seriesId is None:
            RecurrenceEndpoints.cursor.execute("INSERT INTO series () VALUES ();")
            recurrence.seriesId = RecurrenceEndpoints.cursor.lastrowid
        q = recurrence.get_sql_insert_query()
        RecurrenceEndpoints.cursor.execute(q)
        recurrence.recurrenceId = RecurrenceEndpoints.cursor.lastrowid
        MonthsAccessedByUser.generate_recurrence_instances_for_new_recurrence(authentication, recurrence)
        return recurrence.recurrenceId

    @staticmethod
    @router.get("/api/recurrences/{recurrence_id}")
    def get_recurrence(authentication: Authentication, recurrence_id: int):
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        RecurrenceEndpoints.cursor.execute("SELECT * FROM recurrences WHERE recurrence_id = %s", (recurrence_id,))
        res = RecurrenceEndpoints.cursor.fetchone()
        if res["user_id"] != authentication.user_id:
            raise HTTPException(status_code=401, detail="User is not authenticated to access this resource")
        return res, 200

    @staticmethod
    @router.put("/api/recurrences/{recurrence_id}")
    def update_recurrence(authentication: Authentication, recurrence_id: int, recurrence: Recurrence, after: float, inclusive: bool):
        # deletes all future events and regenerates them with the new recurrence rule
        old_recurrence = RecurrenceEndpoints.get_recurrence(authentication, recurrence_id)[0]  # authentication
        MonthsAccessedByUser.delete_recurrence_instances(authentication, recurrence_id, after, inclusive)
        # insert new recurrence
        recurrence.startInstant = after
        recurrence.userId = authentication.user_id
        recurrence.seriesId = old_recurrence["series_id"]
        stmt = recurrence.get_sql_insert_query()
        params = recurrence.get_sql_insert_params()
        RecurrenceEndpoints.cursor.execute(stmt, params)
        recurrence.recurrenceId = RecurrenceEndpoints.cursor.lastrowid
        MonthsAccessedByUser.generate_recurrence_instances_for_new_recurrence(authentication, recurrence)

    @staticmethod
    @router.put("/api/recurrences/{recurrence_id}")
    def set_recurrence_end(authentication: Authentication, recurrence_id: int, end: float):
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        RecurrenceEndpoints.cursor.execute("SELECT * FROM recurrences WHERE recurrence_id = %s", (recurrence_id,))
        res = RecurrenceEndpoints.cursor.fetchone()
        if res["user_id"] != authentication.user_id:
            raise HTTPException(status_code=401, detail="User is not authenticated to modify this resource")
        rule = rrulestr(res[_.RRULE_STRING])
        rrule = rule.replace(until=datetime.datetime.fromtimestamp(end))
        RecurrenceEndpoints.cursor.execute("UPDATE recurrences SET %s = %s WHERE recurrence_id = %s", (_.RRULE_STRING, str(rrule), recurrence_id))

    @staticmethod
    @router.delete("/api/recurrences/{recurrence_id}")
    def delete_recurrence(authentication: Authentication, recurrence_id: int):
        RecurrenceEndpoints.get_recurrence(authentication, recurrence_id)  # authentication
        RecurrenceEndpoints.cursor.execute("DELETE FROM recurrences WHERE recurrence_id = %s", (recurrence_id,))
        return 200, "recurrence successfully deleted"

    @staticmethod
    @router.delete("/api/recurrences/{recurrence_id}")
    def delete_recurrences_after_date(authentication: Authentication, recurrence_id, after: float, inclusive: bool):
        MonthsAccessedByUser.delete_recurrence_instances(authentication, recurrence_id, after, inclusive)
