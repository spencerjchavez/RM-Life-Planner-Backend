from fastapi import APIRouter, HTTPException
from models.Authentication import Authentication
import mysql
from mysql.connector.connection import MySQLCursor, Error
from models.SQLColumnNames import *
from datetime import datetime, timedelta
from dateutil import relativedelta
from models.CalendarEvent import CalendarEvent
from models.ToDo import ToDo
from models.Goal import Goal
from models.Recurrence import Recurrence
from dateutil import rrule
from dateutil.rrule import rrulestr
from endpoints import UserEndpoints

router = APIRouter()
cursor: MySQLCursor

months_accessed_cache: {int: {int: {int: bool}}}  # user_id, year, month, if month has been accessed


# TODO: VALIDATE INPUT FOR RECURRENCE OBJECTS


@router.post("/api/calendar/recurrences")
def create_recurrence(authentication: Authentication, recurrence: Recurrence):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
    if recurrence.userId != authentication.user_id:
        raise HTTPException(status_code=401, detail="User is not authenticated to create this resource")
    if recurrence.goalName is not None and recurrence.todoName is None:
        raise HTTPException(status_code=400, detail="Todo must be created if a goal is defined")
    if recurrence.seriesId is None:
        cursor.execute("INSERT INTO series () VALUES ();")
        recurrence.seriesId = cursor.lastrowid
    q = recurrence.get_sql_insert_query()
    cursor.execute(q)
    recurrence.recurrenceId = cursor.lastrowid
    generate_recurrence_instances_for_new_recurrence(authentication, recurrence)
    return recurrence.recurrenceId


@router.get("/api/calendar/recurrences/{recurrence_id}")
def get_recurrence(authentication: Authentication, recurrence_id: int):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
    cursor.execute("SELECT * FROM recurrences WHERE recurrence_id = %s", (recurrence_id,))
    res = cursor.fetchone()
    if res["user_id"] != authentication.user_id:
        raise HTTPException(status_code=401, detail="User is not authenticated to access this resource")
    return res


@router.put("/api/calendar/recurrences/{recurrence_id}")
def update_recurrence(authentication: Authentication, recurrence_id: int, recurrence: Recurrence,
                      after: float,
                      inclusive: bool):
    # deletes all future events and regenerates them with the new recurrence rule
    old_recurrence = get_recurrence(authentication, recurrence_id)  # authentication
    delete_recurrences_after_date(authentication, recurrence_id, after, inclusive)
    # insert new recurrence
    recurrence.startInstant = after
    recurrence.userId = authentication.user_id
    recurrence.seriesId = old_recurrence["series_id"]
    stmt = recurrence.get_sql_insert_query()
    params = recurrence.get_sql_insert_params()
    cursor.execute(stmt, params)
    recurrence.recurrenceId = cursor.lastrowid
    generate_recurrence_instances_for_new_recurrence(authentication, recurrence)


@router.put("/api/calendar/recurrences/{recurrence_id}")
def set_recurrence_end(authentication: Authentication, recurrence_id: int, end: float):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
    cursor.execute("SELECT * FROM recurrences WHERE recurrence_id = %s", (recurrence_id,))
    res = cursor.fetchone()
    if res["user_id"] != authentication.user_id:
        raise HTTPException(status_code=401, detail="User is not authenticated to modify this resource")
    rule = rrulestr(res[RRULE_STRING])
    rule = rule.replace(until=datetime.fromtimestamp(end))
    cursor.execute("UPDATE recurrences SET %s = %s WHERE recurrence_id = %s",
                   (RRULE_STRING, str(rule), recurrence_id))


@router.delete("/api/calendar/recurrences/{recurrence_id}")
def delete_recurrence(authentication: Authentication, recurrence_id: int):
    get_recurrence(authentication, recurrence_id)  # authentication
    cursor.execute("DELETE FROM recurrences WHERE recurrence_id = %s", (recurrence_id,))
    return "recurrence successfully deleted"


@router.delete("/api/calendar/recurrences/{recurrence_id}")
def delete_recurrences_after_date(authentication: Authentication, recurrence_id, after: float,
                                  inclusive: bool):
    get_recurrence(authentication, recurrence_id)  # authenticate
    cursor.execute("DELETE FROM goals WHERE recurrence_id = %s AND %s %s %s;",
                   (recurrence_id, START_INSTANT, ">=" if inclusive else ">", after))
    cursor.execute("DELETE FROM todos WHERE recurrence_id = %s AND %s %s %s;",
                   (recurrence_id, START_INSTANT, ">=" if inclusive else ">", after))
    cursor.execute("DELETE FROM events WHERE recurrence_id = %s AND %s %s %s",
                   (recurrence_id, START_INSTANT, ">=" if inclusive else ">", after))
    set_recurrence_end(authentication, recurrence_id, after)


#
#
# generate instances of rrule
#
#

def __generate_recurrence_instances_for_month(authentication: Authentication, year: int, month: int):
    cursor.execute("SELECT * FROM recurrences WHERE user_id = %s", (authentication.user_id,))
    res = cursor.fetchall()
    for row in res:
        rrule_str = row[RRULE_STRING]
        rule = rrulestr(rrule_str)
        start_dt = datetime(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_dt = start_dt + relativedelta.relativedelta(months=1) - timedelta(minutes=1)
        occurrences = rule.between(after=start_dt, before=end_dt, inc=True)

        for occurrence in occurrences:
            # is occurrence a datetime?? hopefully...
            __generate_recurrence_instance(authentication, res, occurrence)


def __generate_recurrence_instance(authentication: Authentication, recurrence_dict: {}, dt: datetime):
    goal_id = None
    if recurrence_dict[RECURRENCE_GOAL_NAME] is not None:
        goal = Goal()
        goal.name = recurrence_dict[RECURRENCE_GOAL_NAME]
        goal.userId = recurrence_dict["user_id"]
        goal.desireId = recurrence_dict[RECURRENCE_GOAL_DESIRE_ID]
        goal.howMuch = recurrence_dict[RECURRENCE_GOAL_HOW_MUCH]
        goal.measuringUnits = recurrence_dict[RECURRENCE_GOAL_MEASURING_UNITS]
        goal.timeframe = recurrence_dict[RECURRENCE_GOAL_TIMEFRAME]
        goal.startInstant = dt.timestamp()
        goal.recurrenceId = recurrence_dict[RECURRENCE_ID]
        # create goal
        cursor.execute(
            goal.get_sql_insert_query(),
            goal.get_sql_insert_params())

    todo_id = None
    if recurrence_dict[RECURRENCE_TODO_NAME] is not None:
        todo = ToDo()
        todo.name = recurrence_dict[RECURRENCE_TODO_NAME]
        todo.recurrenceId = recurrence_dict[RECURRENCE_ID]
        todo.userId = recurrence_dict[USER_ID]
        todo.startInstant = dt.timestamp()
        todo.timeframe = recurrence_dict[RECURRENCE_TODO_TIMEFRAME]
        if goal_id is not None:
            todo.linkedGoalId = goal_id
        # create to-do
        cursor.execute(
            todo.get_sql_insert_query(),
            todo.get_sql_insert_params())
        # insert into events_by_user_day
        stmt, params = todo.get_sql_todos_in_day_insert_query_and_params()
        cursor.execute(stmt, params)
    if recurrence_dict[RECURRENCE_EVENT_NAME] is not None:
        event = CalendarEvent()
        event.name = recurrence_dict[RECURRENCE_EVENT_NAME]
        event.description = recurrence_dict[RECURRENCE_EVENT_DESCRIPTION]
        event.startInstant = dt.timestamp()
        event.endInstant = event.startInstant + recurrence_dict[RECURRENCE_EVENT_DURATION]
        event.duration = recurrence_dict[RECURRENCE_EVENT_DURATION]
        event.userId = authentication.user_id
        event.recurrenceId = recurrence_dict[RECURRENCE_ID]
        if goal_id is not None:
            event.linkedGoalId = goal_id
        if todo_id is not None:
            event.linkedTodoId = todo_id
        # create event
        cursor.execute(
            event.get_sql_events_insert_query(),
            event.get_sql_insert_params())
        # insert into events_by_user_day
        stmt, params = event.get_sql_events_in_day_insert_query_and_params()
        cursor.execute(stmt, params)


def generate_recurrence_instances_for_new_recurrence(authentication: Authentication, recurrence: Recurrence):
    year_month_tuples = get_months_accessed_by_user(authentication.user_id)
    for year, month in year_month_tuples:
        rule = rrule.rrulestr(recurrence.rruleString)
        start_dt = datetime(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_dt = start_dt + relativedelta.relativedelta(months=1) - timedelta(minutes=1)
        if end_dt.timestamp() >= recurrence.startInstant:  # if within recurrence timeframe, generate instances, else pass
            occurrences = rule.between(after=start_dt, before=end_dt, inc=True)
            for occurrence in occurrences:
                if occurrence.timestamp() >= recurrence.startInstant:
                    __generate_recurrence_instance(authentication, recurrence.__dict__,
                                                   occurrence)


#
#
# months accessed tracking stuff
#
#
def get_months_accessed_by_user(user_id):
    cursor.execute("SELECT month, year FROM months_accessed_by_user WHERE user_id = %s",
                   user_id)
    res = cursor.fetchall()
    year_month_tuples = []
    for row in res:
        year = row["year"]
        month = row["month"]
        year_month_tuples.append((year, month))
        months_accessed_cache.setdefault(user_id, {}).setdefault(year, {})[month] = True
    return year_month_tuples


def register_month_accessed_by_user(authentication: Authentication, year: int, month: int):
    if not months_accessed_cache.get(authentication.user_id, {}).get(year, {}).get(month,
                                                                                   False):
        cursor.execute(
            "SELECT * FROM months_accessed_by_user WHERE (user_id, year, month) = (%s, %s, %s)",
            (authentication.user_id, year, month))
        if cursor.fetchone() is None:  # month has not been accessed before
            cursor.execute("INSERT INTO months_accessed_by_user (%s, %s, %s)",
                           (authentication.user_id, year, month))
            __generate_recurrence_instances_for_month(authentication, year, month)
        months_accessed_cache.setdefault(authentication.user_id, {}).setdefault(year, {})[
            month] = True
