from fastapi import APIRouter, HTTPException
from models.Authentication import Authentication
from mysql.connector.connection import MySQLCursor
from endpoints import UserEndpoints
from models.SQLColumnNames import SQLColumnNames as _
from datetime import datetime, timedelta
from dateutil import relativedelta
from models.CalendarEvent import CalendarEvent
from models.ToDo import ToDo
from models.Goal import Goal
from models.Recurrence import Recurrence
from dateutil import rrule
from dateutil.rrule import rrulestr


class RecurrenceEndpoints:
    router = APIRouter()
    cursor: MySQLCursor
    months_accessed_cache: {int: {int: {int: bool}}}  # user_id, year, month, if month has been accessed
    user_endpoints: UserEndpoints

    def __init__(self, cursor: MySQLCursor, user_endpoints: UserEndpoints):
        self.cursor = cursor
        self.months_accessed_cache = {}
        self.user_endpoints = user_endpoints

    # TODO: VALIDATE INPUT FOR RECURRENCE OBJECTS

    @router.post("/api/recurrences")
    def create_recurrence(self, authentication: Authentication, recurrence: Recurrence):
        if not self.user_endpoints.authenticate(authentication):
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        if recurrence.userId != authentication.user_id:
            raise HTTPException(status_code=401, detail="User is not authenticated to create this resource")
        if recurrence.seriesId is None:
            self.cursor.execute("INSERT INTO series () VALUES ();")
            recurrence.seriesId = self.cursor.lastrowid
        q = recurrence.get_sql_insert_query()
        self.cursor.execute(q)
        recurrence.recurrenceId = self.cursor.lastrowid
        self.generate_recurrence_instances_for_new_recurrence(authentication, recurrence)
        return recurrence.recurrenceId

    @router.get("/api/recurrences/{recurrence_id}")
    def get_recurrence(self, authentication: Authentication, recurrence_id: int):
        if not self.user_endpoints.authenticate(authentication):
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        self.cursor.execute("SELECT * FROM recurrences WHERE recurrence_id = %s", (recurrence_id,))
        res = self.cursor.fetchone()
        if res["user_id"] != authentication.user_id:
            raise HTTPException(status_code=401, detail="User is not authenticated to access this resource")
        return res, 200

    @router.put("/api/recurrences/{recurrence_id}")
    def update_recurrence(self, authentication: Authentication, recurrence_id: int, recurrence: Recurrence,
                          after: float,
                          inclusive: bool):
        # deletes all future events and regenerates them with the new recurrence rule
        old_recurrence = self.get_recurrence(authentication, recurrence_id)[0]  # authentication
        self.delete_recurrences_after_date(authentication, recurrence_id, after, inclusive)
        # insert new recurrence
        recurrence.startInstant = after
        recurrence.userId = authentication.user_id
        recurrence.seriesId = old_recurrence["series_id"]
        stmt = recurrence.get_sql_insert_query()
        params = recurrence.get_sql_insert_params()
        self.cursor.execute(stmt, params)
        recurrence.recurrenceId = self.cursor.lastrowid
        self.generate_recurrence_instances_for_new_recurrence(authentication, recurrence)

    @router.put("/api/recurrences/{recurrence_id}")
    def set_recurrence_end(self, authentication: Authentication, recurrence_id: int, end: float):
        if not self.user_endpoints.authenticate(authentication):
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        self.cursor.execute("SELECT * FROM recurrences WHERE recurrence_id = %s", (recurrence_id,))
        res = self.cursor.fetchone()
        if res["user_id"] != authentication.user_id:
            raise HTTPException(status_code=401, detail="User is not authenticated to modify this resource")
        rule = rrulestr(res[_.RRULE_STRING])
        rule = rule.replace(until=datetime.fromtimestamp(end))
        self.cursor.execute("UPDATE recurrences SET %s = %s WHERE recurrence_id = %s",
                            (_.RRULE_STRING, str(rule), recurrence_id))

    @router.delete("/api/recurrences/{recurrence_id}")
    def delete_recurrence(self, authentication: Authentication, recurrence_id: int):
        self.get_recurrence(authentication, recurrence_id)  # authentication
        self.cursor.execute("DELETE FROM recurrences WHERE recurrence_id = %s", (recurrence_id,))
        return 200, "recurrence successfully deleted"

    @router.delete("/api/recurrences/{recurrence_id}")
    def delete_recurrences_after_date(self, authentication: Authentication, recurrence_id, after: float,
                                      inclusive: bool):
        self.get_recurrence(authentication, recurrence_id)  # authenticate
        self.cursor.execute("DELETE FROM goals WHERE recurrence_id = %s AND %s %s %s;",
                            (recurrence_id, _.START_INSTANT, ">=" if inclusive else ">", after))
        self.cursor.execute("DELETE FROM todos WHERE recurrence_id = %s AND %s %s %s;",
                            (recurrence_id, _.START_INSTANT, ">=" if inclusive else ">", after))
        self.cursor.execute("DELETE FROM events WHERE recurrence_id = %s AND %s %s %s",
                            (recurrence_id, _.START_INSTANT, ">=" if inclusive else ">", after))
        self.set_recurrence_end(authentication, recurrence_id, after)

    #
    #
    # generate instances of rrule
    #
    #

    def __generate_recurrence_instances_for_month(self, authentication: Authentication, year: int, month: int):
        self.cursor.execute("SELECT * FROM recurrences WHERE user_id = %s", (authentication.user_id,))
        res = self.cursor.fetchall()
        for row in res:
            rrule_str = row[_.RRULE_STRING]
            rule = rrulestr(rrule_str)
            start_dt = datetime(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_dt = start_dt + relativedelta.relativedelta(months=1) - timedelta(minutes=1)
            occurrences = rule.between(after=start_dt, before=end_dt, inc=True)

            for occurrence in occurrences:
                # is occurrence a datetime?? hopefully...
                self.__generate_recurrence_instance(authentication, res, occurrence)

    def __generate_recurrence_instance(self, authentication: Authentication, recurrence_dict: {}, dt: datetime):
        goal_id = None
        if recurrence_dict[_.RECURRENCE_GOAL_NAME] is not None:
            goal = Goal()
            goal.name = recurrence_dict[_.RECURRENCE_GOAL_NAME]
            goal.userId = recurrence_dict["user_id"]
            goal.desireId = recurrence_dict[_.RECURRENCE_GOAL_DESIRE_ID]
            goal.howMuch = recurrence_dict[_.RECURRENCE_GOAL_HOW_MUCH]
            goal.measuringUnits = recurrence_dict[_.RECURRENCE_GOAL_MEASURING_UNITS]
            goal.timeframe = recurrence_dict[_.RECURRENCE_GOAL_TIMEFRAME]
            goal.startInstant = dt.timestamp()
            goal.recurrenceId = recurrence_dict[_.RECURRENCE_ID]
            #create goal
            self.cursor.execute(
                goal.get_sql_insert_query(),
                goal.get_sql_insert_params())

        todo_id = None
        if recurrence_dict[_.RECURRENCE_TODO_NAME] is not None:
            todo = ToDo()
            todo.name = recurrence_dict[_.RECURRENCE_TODO_NAME]
            todo.recurrenceId = recurrence_dict[_.RECURRENCE_ID]
            todo.userId = recurrence_dict[_.USER_ID]
            todo.startInstant = dt.timestamp()
            todo.timeframe = recurrence_dict[_.RECURRENCE_TODO_TIMEFRAME]
            if goal_id is not None:
                todo.linkedGoalId = goal_id
            # create to-do
            self.cursor.execute(
                todo.get_sql_insert_query(),
                todo.get_sql_insert_params())
            # insert into events_by_user_day
            stmt, params = todo.get_sql_todos_in_day_insert_query_and_params()
            self.cursor.execute(stmt, params)
        if recurrence_dict[_.RECURRENCE_EVENT_NAME] is not None:
            event = CalendarEvent()
            event.name = recurrence_dict[_.RECURRENCE_EVENT_NAME]
            event.description = recurrence_dict[_.RECURRENCE_EVENT_DESCRIPTION]
            event.startInstant = dt.timestamp()
            event.endInstant = event.startInstant + recurrence_dict[_.RECURRENCE_EVENT_DURATION]
            event.duration = recurrence_dict[_.RECURRENCE_EVENT_DURATION]
            event.userId = authentication.user_id
            event.recurrenceId = recurrence_dict[_.RECURRENCE_ID]
            if goal_id is not None:
                event.linkedGoalId = goal_id
            if todo_id is not None:
                event.linkedTodoId = todo_id
            # create event
            self.cursor.execute(
                event.get_sql_events_insert_query(),
                event.get_sql_insert_params())
            # insert into events_by_user_day
            stmt, params = event.get_sql_events_in_day_insert_query_and_params()
            self.cursor.execute(stmt, params)

    def generate_recurrence_instances_for_new_recurrence(self, authentication: Authentication, recurrence: Recurrence):
        year_month_tuples = self.get_months_accessed_by_user(authentication.user_id)
        for year, month in year_month_tuples:
            rule = rrule.rrulestr(recurrence.rruleString)
            start_dt = datetime(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_dt = start_dt + relativedelta.relativedelta(months=1) - timedelta(minutes=1)
            if end_dt.timestamp() >= recurrence.startInstant:  # if within recurrence timeframe, generate instances, else pass
                occurrences = rule.between(after=start_dt, before=end_dt, inc=True)
                for occurrence in occurrences:
                    if occurrence.timestamp() >= recurrence.startInstant:
                        self.__generate_recurrence_instance(authentication, recurrence.__dict__,
                                                            occurrence)

    #                   
    #
    # months accessed tracking stuff
    #
    #
    def get_months_accessed_by_user(self, user_id):
        self.cursor.execute("SELECT month, year FROM months_accessed_by_user WHERE user_id = %s",
                            user_id)
        res = self.cursor.fetchall()
        year_month_tuples = []
        for row in res:
            year = row["year"]
            month = row["month"]
            year_month_tuples.append((year, month))
            self.months_accessed_cache.setdefault(user_id, {}).setdefault(year, {})[month] = True
        return year_month_tuples

    def register_month_accessed_by_user(self, authentication: Authentication, year: int, month: int):
        if not self.months_accessed_cache.get(authentication.user_id, {}).get(year, {}).get(month,
                                                                                            False):
            self.cursor.execute(
                "SELECT * FROM months_accessed_by_user WHERE (user_id, year, month) = (%s, %s, %s)",
                (authentication.user_id, year, month))
            if self.cursor.fetchone() is None:  # month has not been accessed before
                self.cursor.execute("INSERT INTO months_accessed_by_user (%s, %s, %s)",
                                    (authentication.user_id, year, month))
                self.__generate_recurrence_instances_for_month(authentication, year, month)
            self.months_accessed_cache.setdefault(authentication.user_id, {}).setdefault(year, {})[
                month] = True
