import datetime
import json
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException
import mysql.connector
from mysql.connector import Error
from models.Recurrence import Recurrence
from models.Authentication import Authentication
from models.CalendarEvent import CalendarEvent
from models.ToDo import ToDo
from endpoints import UserEndpoints
from dateutil.rrule import rrulestr, rrule
from dateutil.relativedelta import relativedelta



class CalendarItemsEndpoint:


    MEASURING_UNIT_CHAR_LIMIT = 12




    @staticmethod
    @router.get("/api/calendar/events")
    def get_calendar_events_and_todos(authentication: Authentication, day: int):
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        # generate repeating events for given day
        # TODO make this a lot faster so we don't need to call it every time we get events for a given day
        monthyear = CalendarItemsEndpoint.get_monthyear_of_day(day)
        CalendarItemsEndpoint.generate_recurrence_events_for_user(user_id, monthyear)


        CalendarItemsEndpoint.cursor.execute(f"SELECT * FROM events_by_user_day WHERE key_id = %s;", (CalendarItemsEndpoint.combine_unsigned_ints_bytes(user_id, day),))
        res = CalendarItemsEndpoint.cursor.fetchone()
        event_ids_bytes = res["event_ids"]
        event_ids_list = [] # WAS BytesHelper.split_bytes_into_list(event_ids_bytes, 4)
        events_list = []
        for event_id in event_ids_list:
            CalendarItemsEndpoint.cursor.execute(
                    f"SELECT * FROM events_by_user_event_id WHERE user_event_id = %s;", (CalendarItemsEndpoint.combine_unsigned_ints_bytes(user_id, event_id),))
            events_list.append(CalendarItemsEndpoint.cursor.fetchone())

        print("retrieved calendar events: " + events_list.__str__())
        return json.dumps(events_list), 200









    @staticmethod
    def get_month_year_from_datetime(dt: datetime):
        return dt.month.__str__() + dt.year.__str__()

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
        start_day_to_check = CalendarItemsEndpoint.get_event_start_day_from_id(event_id_to_check, user_id)
        if start_day < start_day_to_check:
            while True:
                index += 1
                event_id_to_check = children_event_ids[index * 4:index * 4 + 4]
                start_day_to_check = CalendarItemsEndpoint.get_event_start_day_from_id(event_id_to_check, user_id)
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
                start_day_to_check = CalendarItemsEndpoint.get_event_start_day_from_id(event_id_to_check, user_id)
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
    def get_event_start_day_from_id(event_id: str, user_id: str):
        CalendarItemsEndpoint.cursor.execute(f"SELECT * FROM events_by_user_event_id WHERE user_event_id = {user_id}{event_id};")
        return CalendarItemsEndpoint.cursor.fetchone()["start_day"]

    # recurrences stuff
    @staticmethod
    def add_recurrence(authentication: Authentication, recurrence: Recurrence):
        # new recurrence sequence
        CalendarItemsEndpoint.cursor.execute("SELECT * FROM recurrence_ids_by_user WHERE user_id = %s;",
                                              (user_id,))
        recurrence_ids_bytes: bytes = CalendarItemsEndpoint.cursor.fetchone()["recurrence_ids"]
        if len(recurrence_ids_bytes) >= CalendarItemsEndpoint.USER_RECURRENT_LIMIT * 8:
            raise HTTPException(
                detail="User has reached their limit on repeating events. Please delete a repeating event series before creating another one",
                status_code=400)
        # create and add the new recurrence object
        monthyears_buffered_bytes = False.to_bytes(1, "big") * CalendarItemsEndpoint.MONTHYEAR_BUFFER_LIMIT
        CalendarItemsEndpoint.cursor.execute(
            f"INSERT INTO recurrences (user_id, recurrence_type, rrule_string, monthyears_buffered, event_type, event_name, event_description, event_duration, todo_name, todo_timeframe) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
            (user_id, recurrence.recurrenceType, recurrence.rruleString, monthyears_buffered_bytes, recurrence.eventType, recurrence.eventName, recurrence.eventDescription, recurrence.eventDuration, recurrence.todoName, recurrence.todoTimeframe))
        new_recurrence_id = CalendarItemsEndpoint.cursor.lastrowid
        recurrence_ids_bytes = BytesHelper.add_unsigned_bigint_to_bytes(recurrence_ids_bytes, new_recurrence_id)
        # add recurrence id to list of users' recurrence_ids
        CalendarItemsEndpoint.cursor.execute(
            "UPDATE event_recurrence_ids_by_user SET recurrence_ids = %s WHERE user_id = %s",
            (recurrence_ids_bytes, user_id))


    @staticmethod
    def generate_recurrence_events_for_user(user_id: int, monthyear: int):
        # TODO: put error-handling in this function lol
        # check cache to avoid unnecessary api calls
        CalendarItemsEndpoint.cursor.execute(f"SELECT * FROM event_recurrence_ids_by_user WHERE user_id = %s;",
                                              (user_id,))
        recurrence_ids = [] # WAS BytesHelper.split_bytes_into_list(CalendarItemsEndpoint.cursor.fetchone()["recurrence_ids"],
                                     #                      8)
        recurrence_ids_to_generate = []
        for recurrence_id in recurrence_ids:
            try:
                if CalendarItemsEndpoint.users_recurrence_id_monthyears_map[user_id][recurrence_id][monthyear]:
                    return  # don't need to generate more events
            except KeyError:  # need to check if events are generated for monthyear
                CalendarItemsEndpoint.cursor.execute("SELECT * FROM recurrences WHERE recurrence_id = %s",
                                                      (recurrence_id))
                recurrence = CalendarItemsEndpoint.cursor.fetchone()
                monthyears_buffered = recurrence["monthyears_buffered"]
                if bool.from_bytes(monthyears_buffered[monthyear], "big"):
                    # monthyears already generated
                    CalendarItemsEndpoint.users_recurrence_id_monthyears_map[user_id][recurrence_id][monthyear] = True
                    return
                else:  # need to generate events
                    recurrence_ids_to_generate.append(recurrence_id)
                    # update monthyears
                    monthyears_buffered[monthyear] = True.to_bytes(1, "big")
                    CalendarItemsEndpoint.cursor.execute(
                        "ALTER TABLE recurrences SET monthyears_buffered = %s WHERE recurrence_id IN %s",
                        (monthyears_buffered, recurrence_id))


            res = CalendarItemsEndpoint.cursor.fetchone()
            recurrence_type = res["recurrence_type"]
            rrule_string = res["rrule_string"]

            event_name = res["event_name"]
            event_description = res["event_description"]
            event_type = res["event_type"]
            event_duration = res["event_duration"]

            todo_name = res["todo_name"]
            todo_timeframe = res["todo_timeframe"]

            month_start = CalendarItemsEndpoint.get_datetime_from_monthyear(monthyear)
            month_end = month_start + relativedelta(months=1) - relativedelta(seconds=1)
            _rrule: rrule = rrulestr(rrule_string)
            event_datetimes: [datetime] = _rrule.between(after=month_start, before=month_end, inc=True)

            # insert events into database baby!
            if len(event_datetimes) == 0:
                return

            if recurrence_type == CalendarItemsEndpoint.RecurrenceType.EventOnly or recurrence_type == CalendarItemsEndpoint.RecurrenceType.Both:
                # generate calendar events
                sql_statement = "INSERT INTO events_by_user_event_id (key_id, name, description, event_type, start_instant, start_day, end_instant, end_day, duration, recurrence_id) " \
                             "VALUES %s;"
                sql_values = ""
                sql_value_statement = "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s),"
                event_ids = []
                for _datetime in event_datetimes:
                    _datetime: datetime = _datetime
                    event_id = CalendarItemsEndpoint.get_next_event_id(user_id)
                    event_ids.append(event_id)
                    key_id = CalendarItemsEndpoint.combine_unsigned_ints_bytes(user_id, event_id)
                    end_instant = _datetime.timestamp() + event_duration
                    end_day = CalendarItemsEndpoint.get_day_of_instant(end_instant)
                    sql_values += (sql_value_statement, (key_id, event_name, event_description, event_type, _datetime.timestamp(), CalendarItemsEndpoint.get_day_of_instant(_datetime.timestamp()), end_instant, end_day, event_duration, recurrence_id))
                CalendarItemsEndpoint.cursor.execute(sql_statement, (sql_values[:len(sql_values) - 1]))
                # add events to events_by_user_day
                index = 0
                for _datetime in event_datetimes:
                    key_id = CalendarItemsEndpoint.combine_unsigned_ints_bytes(user_id, CalendarItemsEndpoint.get_day_of_instant(int(_datetime.timestamp())))
                    CalendarItemsEndpoint.cursor.execute(
                        "SELECT * FROM events_by_user_day WHERE key_id = %s", (key_id,))
                    event_ids_bytes = CalendarItemsEndpoint.cursor.fetchone()["event_ids"]
                    event_ids_bytes = BytesHelper.add_unsigned_int_to_bytes(event_ids_bytes, event_ids[index])

                    CalendarItemsEndpoint.cursor.execute(
                        "ALTER events_by_user_day SET event_ids = %s WHERE key_id = %s", (event_ids_bytes, key_id))
                    index += 1

            if recurrence_type == CalendarItemsEndpoint.RecurrenceType.TodoOnly or recurrence_type == CalendarItemsEndpoint.RecurrenceType.Both:
                # generate todos!
                sql_statement = "INSERT INTO todos_by_user_todo_id (key_id, name, timeframe, start_day, recurrence_id) " \
                                "VALUES %s;"
                sql_values = ""
                sql_value_statement = "(%s, %s, %s, %s, %s),"
                for _datetime in event_datetimes:
                    _datetime: datetime = _datetime
                    todo_id = CalendarItemsEndpoint.get_next_todo_id(user_id)
                    user_todo_key_id = CalendarItemsEndpoint.combine_unsigned_ints_bytes(user_id, todo_id)
                    sql_values += (sql_value_statement, (user_todo_key_id, todo_name, todo_timeframe, CalendarItemsEndpoint.get_day_of_instant(_datetime.timestamp()), recurrence_id))

                    # also add to todos_by_user_day
                    user_day_key_id = CalendarItemsEndpoint.combine_unsigned_ints_bytes(user_id,
                                                                                CalendarItemsEndpoint.get_day_of_instant(
                                                                                    int(_datetime.timestamp())))
                    CalendarItemsEndpoint.cursor.execute(
                        "SELECT * FROM todos_by_user_day WHERE key_id = %s", (user_day_key_id,))
                    todo_ids_bytes = CalendarItemsEndpoint.cursor.fetchone()["todo_ids"]
                    todo_ids_bytes = [] # BytesHelper.add_unsigned_int_to_bytes(todo_ids_bytes, todo_id)
                    CalendarItemsEndpoint.cursor.execute(
                        "ALTER todos_by_user_day SET todo_ids = %s WHERE key_id = %s", (todo_ids_bytes, user_day_key_id))

                CalendarItemsEndpoint.cursor.execute(sql_statement, (sql_values[:len(sql_values) - 1]))

    @staticmethod
    def get_day_of_instant(instant: float):
        return int(datetime.fromtimestamp(instant).replace(hour=0, minute=0, second=0).timestamp())

    @staticmethod
    def combine_unsigned_ints_bytes(a: int, b: int):
        return int.from_bytes(a.to_bytes(4, "big", signed=False).join(b.to_bytes(4, "big", signed=False)), byteorder="big", signed=False)

    @staticmethod
    def get_monthyear_of_day(day: int):
        dt = datetime.fromtimestamp(day)
        return (dt.year - 1970) * 12 + dt.month - 1

    @staticmethod
    def get_datetime_from_monthyear(monthyear: int):
        year = int(monthyear / 12) + 1970
        month = monthyear % 12 + 1 # january = 1, december = 12
        return datetime(year=year, month=month, day=1)

    @staticmethod
    def get_next_event_id(user_id: int):
        CalendarItemsEndpoint.cursor.execute("SELECT * FROM users WHERE user_id = %s", user_id)
        res = CalendarItemsEndpoint.cursor.fetchone()
        if res is None:
            raise HTTPException(detail="Invalid user_id provided", status_code=400)
        event_id = res["next_event_id"]
        events_owned = res["events_owned"]
        if events_owned >= CalendarItemsEndpoint.USER_EVENT_LIMIT:
            raise HTTPException(detail=(
            f"User has reached the maximum number of events allowed, (%s) please delete past events before creating any new ones.",
            CalendarItemsEndpoint.USER_EVENT_LIMIT.__str__()), status_code=400)
        CalendarItemsEndpoint.cursor.execute(
            "UPDATE users SET next_event_id = %s, events_owned = %s, WHERE user_id = %s",
            (event_id + 1, events_owned, user_id))
        return event_id

    @staticmethod
    def get_next_todo_id(user_id: int):
        CalendarItemsEndpoint.cursor.execute("SELECT * FROM users WHERE user_id = %s", user_id)
        res = CalendarItemsEndpoint.cursor.fetchone()
        if res is None:
            raise HTTPException(detail="Invalid user_id provided", status_code=400)
        todo_id = res["next_todo_id"]
        todos_owned = res["todo_owned"]
        if todos_owned >= CalendarItemsEndpoint.USER_TODO_LIMIT:
            raise HTTPException(detail=(
                f"User has reached the maximum number of events allowed, (%s) please delete past events before creating any new ones.",
                CalendarItemsEndpoint.USER_TODO_LIMIT.__str__()), status_code=400)
        CalendarItemsEndpoint.cursor.execute(
            "UPDATE users SET next_todo_id = %s, todos_owned = %s, WHERE user_id = %s",
            (todo_id + 1, todos_owned + 1, user_id))
        return todo_id