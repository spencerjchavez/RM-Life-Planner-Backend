import datetime
import json
from datetime import datetime

import fastapi
from fastapi import APIRouter, HTTPException
from mysql.connector.cursor import MySQLCursor
from models.CalendarEvent import CalendarEvent
from endpoints import UserEndpoints
from models.Authentication import Authentication
from endpoints.MonthsAccessedByUserEndpoints import MonthsAccessedByUser


class CalendarEventEndpoints:
    #TODO: make sure IN ALL ENDPOINTS when a user creates a resource the user_id matches

    router = APIRouter()
    cursor: MySQLCursor

    @staticmethod
    @router.post("/api/calendar/events")
    def create_calendar_event(authentication: Authentication, event: CalendarEvent):
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)

        CalendarEventEndpoints.cursor.execute(
            event.get_sql_events_insert_query(),
            event.get_sql_insert_params())

        # insert into events_by_user_day
        stmt, params = event.get_sql_events_in_day_insert_query_and_params()
        CalendarEventEndpoints.cursor.execute(stmt, params)
        return {"message": "event successfully added", "event_id": event.eventId}, 200

    @staticmethod
    @router.get("/api/calendar/events")
    def get_calendar_events(authentication: Authentication, start_day: int, end_day: int):
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        dt = datetime.fromtimestamp(start_day)
        event_ids = set()
        while dt.timestamp() <= end_day:
            dt.replace(hour=0, minute=0, second=0, microsecond=0)
            year = dt.year
            month = dt.month
            # register that we are accessing month to generate recurrence events
            MonthsAccessedByUser.register_month_accessed_by_user(authentication, year, month)
            CalendarEventEndpoints.cursor.execute("SELECT event_id FROM events_in_day WHERE day = %s AND user_id = %s", (dt.timestamp(), authentication.user_id))
            res = CalendarEventEndpoints.cursor.fetchall()
            for row in res:
                event_ids.add(row["event_id"])
            dt += datetime.timedelta(days=1)

        stmt = ""
        for event_id in event_ids:
            stmt += f"SELECT * FROM events WHERE event_id = {event_id};"
        CalendarEventEndpoints.cursor.execute(stmt, multi=True)
        res = CalendarEventEndpoints.cursor.fetchall()
        return {"events": res}, 200


    @staticmethod
    @router.put("/api/calendar/events/{event_id}")
    def update_calendar_event(authentication: Authentication, event_id: int, event: CalendarEvent):
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        if event_id != event.eventId:
            raise HTTPException(detail="event_id provided in parameter does not match event_id of the object provided",
                                status_code=400)
        if event.userId != user_id:
            raise HTTPException(detail="user is not authorized to access this resource!", status_code=401)

        key_id = CalendarEventEndpoints.combine_unsigned_ints_bytes(user_id, event.eventId)
        event.startDay = CalendarEventEndpoints.get_day_of_instant(event.startInstant)
        event.endDay = CalendarEventEndpoints.get_day_of_instant(event.endInstant)

        CalendarEventEndpoints.cursor.execute("SELECT * FROM events_by_user_event_id WHERE key_id = %s", key_id)
        res = CalendarEventEndpoints.cursor.fetchone()
        # figure out what events_by_user_day entries we need to update!
        old_event_days = []
        start_datetime = datetime.fromtimestamp(res["start_day"])
        while True:
            old_event_days.append(start_datetime)
            if start_datetime.timestamp() >= res["end_day"]:
                break
            start_datetime + datetime.timedelta(days=1)

        new_event_days = []
        start_datetime = datetime.fromtimestamp(event.startDay)
        while True:
            new_event_days.append(start_datetime)
            if start_datetime.timestamp() >= event.endDay:
                break
            start_datetime + datetime.timedelta(days=1)

        days_to_remove = []
        days_to_add = []
        for day in old_event_days:
            if new_event_days.__contains__(day):
                new_event_days.remove(day)
            else:
                days_to_remove.append(day)

        days_to_add = new_event_days

        # add event_id to days
        for day in days_to_add:
            key_id = CalendarEventEndpoints.combine_unsigned_ints_bytes(user_id, day.timestamp().__int__())
            CalendarEventEndpoints.cursor.execute("SELECT * FROM events_by_user_day WHERE key_id = %s", key_id)
            res = CalendarEventEndpoints.cursor.fetchone()
            # new_bytes = BytesHelper.add_unsigned_int_to_bytes(res["event_ids"], event_id)
            # CalendarEventEndpoints.cursor.execute("ALTER events_by_user_day SET event_ids = %s WHERE key_id = %s",
            #                                     (new_bytes, key_id))
        # remove event_id from days
        for day in days_to_remove:
            key_id = CalendarEventEndpoints.combine_unsigned_ints_bytes(user_id, day.timestamp().__int__())
            CalendarEventEndpoints.cursor.execute("SELECT * FROM events_by_user_day WHERE key_id = %s", key_id)
            res = CalendarEventEndpoints.cursor.fetchone()
            # new_bytes = BytesHelper.remove_unsigned_int_from_bytes(res["event_ids"], event_id)
            # CalendarEventEndpoints.cursor.execute("ALTER events_by_user_day SET event_ids = %s WHERE key_id = %s",
            #                                      (new_bytes, key_id))

        key_id = CalendarEventEndpoints.combine_unsigned_ints_bytes(user_id, event.eventId)
        CalendarEventEndpoints.cursor.execute(
            "ALTER events_by_user_event_id SET name = %s, description = %s, event_type = %s, start_instant = %s, start_day = %s, end_instant = %s, end_day = %s, duration = %s WHERE key_id = %s",
            (event.name, event.description, event.eventType, event.startInstant, event.startDay, event.endInstant,
             event.endDay, event.duration, key_id))

        # yuhhhhhh
        return 200

    @staticmethod
    @router.delete("/api/calendar/events/{event_id}")
    def delete_event(authentication: Authentication, event_id: int):
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        CalendarEventEndpoints.cursor.execute(f"SELECT * FROM events_by_user_event_id WHERE user_event_id = %s;",
                                             user_id.__str__() + event_id.__str__())
        res = CalendarEventEndpoints.cursor.fetchone()
        if res is None:
            raise HTTPException(detail=f"event of id: {event_id} could not be found", status_code=404)
        day = res["start_day"]
        CalendarEventEndpoints.cursor.execute(f"DELETE FROM events_by_user_event_id WHERE user_event_id = %s;",
                                             (user_id.__str__() + event_id.__str__()), )
        CalendarEventEndpoints.cursor.execute(f"DELETE FROM events_by_user_day WHERE key_id = %s;",
                                             (user_id.__str__() + day.__str__), )
        return f"successfully deleted event with id: '{event_id}'", 200

    @staticmethod
    @router.delete("/api/calendar/events")
    def delete_events_of_user(authentication: Authentication):
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        CalendarEventEndpoints.cursor.execute(
            f"DELETE FROM events_by_user_event_id WHERE user_event_id BETWEEN %s AND %s;",
            (user_id.__str__() + "000000000", (user_id + 1).__str__() + "000000000"))
        CalendarEventEndpoints.cursor.execute(
            f"DELETE FROM events_by_user_day WHERE key_id BETWEEN %s AND %s;",
            (user_id.__str__() + "000000000", (user_id + 1).__str__() + "000000000"))
        return "successfully deleted user_id + " + user_id.__str__() + "!!", 200
