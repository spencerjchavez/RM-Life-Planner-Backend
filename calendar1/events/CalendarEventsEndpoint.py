import copy
import datetime
import json
from datetime import time, datetime
import calendar
from fastapi import APIRouter, HTTPException
import mysql.connector
from mysql.connector import Error
from fastapi import Response
import Routes
from calendar1.events.CalendarEvent import CalendarEvent
from calendar1.events.CalendarEventAsParameter import CalendarEventAsParameter
from users import UsersEndpoint
from dateutil.rrule import rrulestr, rrule


router = APIRouter()


class CalendarEventsEndpoint:
    recurrent_event_limit = 5000  # number of events that can be attached to one recurrence_id
    user_recurrent_limit = 500  # number of recurrent_ids that can be attached to each user
    monthyear_buffer_limit = 1200 / 6  # max number of monthyears that can be buffered for a single event
    day_in_seconds = 86401

    try:
        connection = mysql.connector.connect(
            host='34.31.57.31',
            database='calendars',
            user='root',
            password='supersecretdatabase$$keepout',
            autocommit=True
        )
        cursor = connection.cursor(dictionary=True)
        if connection.is_connected():
            print('Connected to calendars database')
    except Error as e:
        print(f'Error connecting to MySQL database: {e}')

    @staticmethod
    @router.post("/api/calendar/events")
    def add_calendar_event(user_id: int, api_key: str, event: CalendarEventAsParameter):
        if not UsersEndpoint.authenticate(user_id, api_key):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        CalendarEventsEndpoint.cursor.execute("SELECT MAX(user_event_id) FROM events_by_user_event_id WHERE user_event_id < %s;", ((user_id + 1).__str__() + "000000000",))
        res = CalendarEventsEndpoint.cursor.fetchone()
        user_event_id = res["user_event_id"] + 1 if res is not None else "100000000"
        event_id = user_event_id[10:]
        if event.recurrenceId is None:
            # new recurrence sequence
            CalendarEventsEndpoint.cursor.execute("SELECT * FROM recurrence_ids_by_user WHERE user_id = %s;", (user_id,))
            recurrence_ids_string: str = CalendarEventsEndpoint.cursor.fetchone()[1]
            if len(recurrence_ids_string) >= CalendarEventsEndpoint.user_recurrent_limit * 8:
                raise HTTPException(detail="User has reached their limit on repeating events. Please delete a repeating event series before creating another one", status_code=400)
            #create and add the new recurrence object
            CalendarEventsEndpoint.cursor.execute(f"INSERT INTO recurrences_by_id COLUMNS (user_id, rrule_string) VALUES (%s, %s);", (user_id, event.rruleString))
            new_recurrence_id = CalendarEventsEndpoint.cursor.lastrowid
            recurrence_ids_string += new_recurrence_id  # add recurrence id to list of users' recurrence_ids
            event.recurrenceId = int(new_recurrence_id)
        else:
            # recurrence sequence already defined, this is just a child event of the sequence
            # inserting event_id into the recurrence children_event_ids should be handled separately
            pass

        # insert into events_by_user_event_id
        CalendarEventsEndpoint.cursor.execute(f"INSERT INTO events_by_user_event_id (name, description, start_time, end_time, start_day, duration, rrule, recurrence_id, happened, report, event_type, user_event_id) "
                                              f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", (event.name, event.description, event.startInstant, event.endInstant, event.startDay, event.duration, event.rruleString, event.recurrenceId, event.happened, event.report, event.eventType, user_event_id))
        # insert into recurrent_ids_by_user if applicable
        if event.recurrenceId is not None:
            CalendarEventsEndpoint.cursor.execute(f"SELECT * FROM recurrences_by_id WHERE recurrence_id = %s;", (event.recurrenceId))
            new_event_ids_string = CalendarEventsEndpoint.cursor.fetchall()[0]["children_event_ids"] + event.eventId.__str__()
            CalendarEventsEndpoint.cursor.execute(f"UPDATE recurrences_by_id SET childen_event_ids =  %s WHERE recurrence_id = %s;", (new_event_ids_string, event.recurrenceId))

        # insert into events_by_user_day
        day = event.startDay
        key_id = f"{user_id}{day.__str__()[:9]}"
        CalendarEventsEndpoint.cursor.execute(f"SELECT * FROM events_by_user_day WHERE key_id = %s;", (key_id,))
        row = CalendarEventsEndpoint.cursor.fetchone()
        if row is None:
            CalendarEventsEndpoint.cursor.execute(f"INSERT INTO events_by_user_day (key_id, event_ids) VALUES (%s, %s);", (key_id, event_id))
        else:
            #throw event_id at the end of the event_ids attribute
            event_ids = row[1] + event_id
            CalendarEventsEndpoint.cursor.execute(f"UPDATE events_by_user_day SET event_ids = %s WHERE key_id = %s;", (event_ids, key_id))
        return {"message": "event successfully added", "event_id" : event_id.__str__()}, 200,

    @staticmethod
    def generate_repeating_events(user_id: int, api_key: str, recurrence_id: int, month: datetime.month, year: datetime.year):
        if not UsersEndpoint.authenticate(user_id, api_key):
            return "User is not authenticated, please log in", 401
        CalendarEventsEndpoint.cursor.execute("SELECT * FROM recurrences_by_id WHERE recurrence_id = %s;", (recurrence_id,))
        monthyears_buffered_string = CalendarEventsEndpoint.cursor.fetchone()["monthyears_buffered"]
        children_event_ids_string = CalendarEventsEndpoint.cursor.fetchone()["childen_event_ids"]
        event_name = CalendarEventsEndpoint.cursor.fetchone()["event_name"]
        event_description = CalendarEventsEndpoint.cursor.fetchone()["event_description"]
        event_type = CalendarEventsEndpoint.cursor.fetchone()["event_type"]
        rrule_string = CalendarEventsEndpoint.cursor.fetchone()["rrule_string"]
        event_end = CalendarEventsEndpoint.cursor.fetchone()["event_end_time"]

        if len(monthyears_buffered_string) / 6 >= CalendarEventsEndpoint.monthyear_buffer_limit:
            raise HTTPException(detail=f"Cannot generate more events of recurrence_id: {recurrence_id}. Please create a new repeating event series instead", status_code=400)

        new_string, was_inserted, index_inserted = CalendarEventsEndpoint.insert_monthyear_into_monthyears_string(monthyears_buffered_string, month, year)
        if not was_inserted:
            return f"monthyear {month}{year} was already generated silly"

        rrule = rrulestr(rrule_string)
        event_start: datetime = rrule.dtstart
        event_duration = event_end - event_start.timestamp()
        x = datetime(month=month, year=year, day=event_start.day if event_start.month == month and event_start.year == year else 0, minute=rrule._dtstart.minute, hour=rrule._dtstart.hour)
        x = rrule.after(x, True)
        while x.month == month and x.year == year:  # if finished generating events in this monthyear
            event_day = datetime(day=x.day, month=x.month, year=x.year).timestamp()
            event = CalendarEventAsParameter(name=event_name, description=event_description, startInstant=x.timestamp(), startDay=event_day, endInstant=x.timestamp() + event_duration, recurrenceId=recurrence_id, event_type=event_type, rruleString=rrule_string)
            res = CalendarEventsEndpoint.add_calendar_event(user_id, api_key, event)

            event_id = res[0]["event_id"]
            # TODO: in the future, need to modify the insert_event_id function so that it can take in
            #  the entire string of event ids and insert them all at the same time instead of doing each on individually
            children_event_ids_string = CalendarEventsEndpoint.insert_event_id_into_children_events_string(children_event_ids_string, event_id, event.startDay, user_id.__str__(), index_inserted)
            # insert into database baby!
            CalendarEventsEndpoint.cursor.execute(
                f"UPDATE recurrences_by_id SET children_event_ids = %s WHERE recurrence_id = %s;", (children_event_ids_string, recurrence_id))
            x = rrule.after(x)
            CalendarEventsEndpoint.add_calendar_event(user_id, api_key, event)
        return "successfully generated events!", 200

    @staticmethod
    @router.put("/api/calendar/events/{event_id}")
    def update_calendar_event(user_id: int, api_key: str, event_id: int, event: CalendarEventAsParameter):
        if event_id != event.eventId:
            raise HTTPException(detail="event_id provided in parameter does not match event_id of the object provided", status_code=400)
        CalendarEventsEndpoint.delete_event(user_id, api_key, event_id)
        return CalendarEventsEndpoint.add_calendar_event(user_id, api_key, event)

    @staticmethod
    @router.get("/api/calendar/events")
    def get_calendar_events(user_id: int, api_key: str, start_day: int, end_day: int):
        if not UsersEndpoint.authenticate(user_id, api_key):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        CalendarEventsEndpoint.cursor.execute(f"SELECT * FROM events_by_user_day WHERE key_id BETWEEN %s AND %s;", ((user_id.__str__() + start_day.__str__())[:19], (user_id.__str__() + (end_day + CalendarEventsEndpoint.day_in_seconds).__str__())[:19]))
        res_list = CalendarEventsEndpoint.cursor.fetchall()
        events_list = []
        for row in res_list:
            events_str = row["event_ids"]
            event_ids = CalendarEventsEndpoint.split_string_into_substrings(events_str, 9)
            for event_id in event_ids:
                CalendarEventsEndpoint.cursor.execute(
                    f"SELECT * FROM events_by_user_event_id WHERE user_event_id = %s;", ((user_id.__str__() + event_id)[:19]),)
                events_list += CalendarEventsEndpoint.cursor.fetchone().__dict__

        print("retrieved calendar events: " + events_list.__str__())
        return json.dumps(events_list), 200

    @staticmethod
    @router.get("/api/calendar/events")
    def get_calendar_events(self, user_id: int, api_key: str, day: int):
        if not UsersEndpoint.authenticate(user_id, api_key):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        # generate repeating events for given day
        # TODO make this a lot faster so we don't need to call it every time we get events for a given day
        dt = datetime.fromtimestamp(day)
        CalendarEventsEndpoint.cursor.execute(f"SELECT * FROM recurrences_by_user WHERE user_id = %s;", (user_id,))
        recurrence_ids = CalendarEventsEndpoint.split_string_into_substrings(CalendarEventsEndpoint.cursor.fetchone()["recurrence_ids"], 8)
        for recurrence_id in recurrence_ids:
            CalendarEventsEndpoint.generate_repeating_events(user_id, api_key, int(recurrence_id), dt.month, dt.year)

        res = self.calendars_cursor.execute(f"SELECT * FROM events_by_user_day WHERE key_id = %s;", (user_id.__str__() + day.__str__())[:19])
        res_list = CalendarEventsEndpoint.cursor.fetchall()
        events_list = []
        for row in res_list:
            events_str = row["event_ids"]
            event_ids = CalendarEventsEndpoint.split_string_into_substrings(events_str, 4)
            for event_id in event_ids:
                CalendarEventsEndpoint.cursor.execute(
                    f"SELECT * FROM events_by_user_event_id WHERE user_event_id = %s;", (user_id.__str__() + event_id)[:19])
                events_list += CalendarEventsEndpoint.cursor.fetchone()

        print("retrieved calendar events: " + events_list.__str__())
        return json.dumps(events_list), 200

    @staticmethod
    @router.delete("/api/calendar/events/{event_id}")
    def delete_event(user_id: int, api_key: str, event_id: int):
        if not UsersEndpoint.authenticate(user_id, api_key):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        CalendarEventsEndpoint.cursor.execute(f"SELECT * FROM events_by_user_event_id WHERE user_event_id = %s;", user_id.__str__() + event_id.__str__())
        res = CalendarEventsEndpoint.cursor.fetchone()
        if res is None:
            raise HTTPException(detail=f"event of id: {event_id} could not be found", status_code=404)
        day = res["start_day"]
        CalendarEventsEndpoint.cursor.execute(f"DELETE * FROM events_by_user_event_id WHERE user_event_id = %s;", (user_id.__str__() + event_id.__str__()),)
        CalendarEventsEndpoint.cursor.execute(f"DELETE * FROM events_by_user_day WHERE key_id = %s;", (user_id.__str__() + day.__str__),)
        return f"successfully deleted event with id: '{event_id}'", 200

    @staticmethod
    @router.delete("/api/calendar/events")
    def delete_events_of_user(user_id: int, api_key: str):
        if not UsersEndpoint.authenticate(user_id, api_key):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        CalendarEventsEndpoint.cursor.execute(
            f"DELETE * FROM events_by_user_event_id WHERE user_event_id BETWEEN %s AND %s;", (user_id.__str__() + "000000000", (user_id+1).__str__() + "000000000"))
        CalendarEventsEndpoint.cursor.execute(
            f"DELETE * FROM events_by_user_day WHERE key_id BETWEEN %s AND %s;", (user_id.__str__() + "000000000", (user_id+1).__str__() + "000000000"))
        return "successfully deleted user_id + " + user_id.__str__() + "!!", 200

    @staticmethod
    def split_string_into_substrings(string: str, len_of_substrings):
        return [string[i:i + len_of_substrings] for i in range(0, len(string), len_of_substrings)]

    @staticmethod
    def get_month_year_from_datetime(dt: datetime):
        return dt.month.__str__() + dt.year.__str__()

    @staticmethod
    def generate_new_recurrence_id_for_table(table_name: str):
        CalendarEventsEndpoint.cursor.execute(f"SELECT MAX(recurrence_id) in {table_name};")
        res = CalendarEventsEndpoint.cursor.fetchone()
        return (res[0][0] + 1) if res is not None else 0

    @staticmethod
    def insert_monthyear_into_monthyears_string(monthyears_string: str, month: datetime.month, year: datetime.year):
        # maintains string ordering so that earliest dates appear earliest in the string
        new_month_year_string = month.__str__ + year.__str__
        for i in range(0, len(monthyears_string), 6):
            if monthyears_string[i:i+6] > new_month_year_string:
                monthyears_string = monthyears_string[:i] + new_month_year_string + monthyears_string [i:]
                return monthyears_string, True, int(i/6)
            if monthyears_string[i:i+6] == new_month_year_string:
                return monthyears_string, False, None
        print(f"ERROR: MONTH YEAR: {new_month_year_string} could not be added to monthyears_string: {monthyears_string}\nTHIS SHOULD NOT HAVE HAPPENED DS:")
        return None, False, None

    @staticmethod
    def insert_event_id_into_children_events_string(children_event_ids: str, event_id: str, start_day: int, user_id: str, index_hint):
        # maintains ordering so that earliest events appear earliest in the string
        # index hint gives a hint of where to start searching for the right place to input the event_id
        index = index_hint
        event_id_to_check = children_event_ids[index*4:index*4 + 4]
        start_day_to_check = CalendarEventsEndpoint.get_event_start_day_from_id(event_id_to_check, user_id)
        if start_day < start_day_to_check:
            while True:
                index += 1
                event_id_to_check = children_event_ids[index * 4:index * 4 + 4]
                start_day_to_check = CalendarEventsEndpoint.get_event_start_day_from_id(event_id_to_check, user_id)
                if start_day > start_day_to_check:
                    #found where to insert
                    children_event_ids = children_event_ids[:index*4] + event_id + children_event_ids[index*4:]
                    return children_event_ids, True
                elif start_day == start_day_to_check:
                    print(f"THIS SHOULDN'T HAVE HAPPENED!! EVENT OF ID: {event_id} COULD NOT BE ADDED INTO CHILDREN EVENT IDS STRING BECAUSE THERE IS ALREADY EVENT WITH THE SAME DATE!\nThat event has id: {event_id_to_check}")
                if index*4 >= len(children_event_ids):
                    print(
                        f"THIS SHOULDN'T HAVE HAPPENED!! EVENT OF ID: {event_id} COULD NOT BE ADDED INTO CHILDREN EVENT IDS STRING: {children_event_ids}")
                    return children_event_ids, False
        elif start_day > start_day_to_check:
            while True:
                index -= 1
                event_id_to_check = children_event_ids[index * 4:index * 4 + 4]
                start_day_to_check = CalendarEventsEndpoint.get_event_start_day_from_id(event_id_to_check, user_id)
                if start_day < start_day_to_check:
                    # found where to insert
                    children_event_ids = children_event_ids[:index * 4] + event_id + children_event_ids[index * 4:]
                    return children_event_ids, True
                elif start_day == start_day_to_check:
                    print(
                        f"THIS SHOULDN'T HAVE HAPPENED!! EVENT OF ID: {event_id} COULD NOT BE ADDED INTO CHILDREN EVENT IDS STRING BECAUSE THERE IS ALREADY EVENT WITH THE SAME DATE!\nThat event has id: {event_id_to_check}")
                if index <= 0:
                    print(
                        f"THIS SHOULDN'T HAVE HAPPENED!! EVENT OF ID: {event_id} COULD NOT BE ADDED INTO CHILDREN EVENT IDS STRING: {children_event_ids}")
                    return children_event_ids, False
        else:
            print(f"THIS SHOULDN'T HAVE HAPPENED!! EVENT OF ID: {event_id} COULD NOT BE ADDED INTO CHILDREN EVENT IDS STRING BECAUSE THERE IS ALREADY EVENT WITH THE SAME DATE!\nThat event has id: {event_id_to_check}")
            return children_event_ids, False


    @staticmethod
    def get_event_start_day_from_id(event_id:str, user_id: str):
        CalendarEventsEndpoint.cursor.execute(f"SELECT * FROM events_by_user_event_id WHERE user_event_id = {user_id}{event_id};")
        return CalendarEventsEndpoint.cursor.fetchone()["start_day"]

