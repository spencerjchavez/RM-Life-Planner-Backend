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
from endpoints import UserEndpoints, GoalAchievingEndpoints, CalendarToDoEndpoints, CalendarEventEndpoints

router = APIRouter()
cursor: MySQLCursor

months_accessed_cache: {int: {int: {int: bool}}}  # user_id, year, month, if month has been accessed


@router.post("/api/calendar/recurrences")
def create_recurrence(authentication: Authentication, recurrence: Recurrence):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
    __validate_recurrence(authentication, recurrence)
    q = recurrence.get_sql_insert_query()
    cursor.execute(q)
    recurrence.recurrenceId = cursor.lastrowid
    __generate_recurrence_instances_for_new_recurrence(authentication, recurrence)
    return {"recurrence_id": recurrence.recurrenceId}


@router.get("/api/calendar/recurrences/{recurrence_id}")
def get_recurrence(authentication: Authentication, recurrence_id: int):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
    cursor.execute("SELECT * FROM recurrences WHERE recurrence_id = %s", (recurrence_id,))
    res = cursor.fetchone()
    if res["user_id"] != authentication.user_id:
        raise HTTPException(status_code=401, detail="User is not authenticated to access this resource")
    recurrence = Recurrence.from_sql_res(res.__dict__)
    return {"recurrence": recurrence}


@router.put("/api/calendar/recurrences/{recurrence_id}")
def update_recurrence(authentication: Authentication, recurrence_id: int, updated_recurrence: Recurrence,
                      after: float,
                      inclusive: bool):
    # authenticate
    _ = get_recurrence(authentication, recurrence_id)
    __validate_recurrence(authentication, updated_recurrence)
    delete_recurrence_instances_after_date(authentication, recurrence_id, after, inclusive)
    # insert new recurrence
    updated_recurrence.startInstant = after
    cursor.execute(
        "UPDATE recurrences SET %s = %s, %s = %s, %s = %s, %s = %s, %s = %s, %s = %s, %s = %s, %s = %s, %s = %s, %s = %s, %s = %s, %s = %s WHERE recurrence_id = %s",
        (START_INSTANT, updated_recurrence.startInstant,
         RRULE_STRING, updated_recurrence.rruleString,
         RECURRENCE_EVENT_NAME, updated_recurrence.eventName,
         RECURRENCE_EVENT_DESCRIPTION, updated_recurrence.eventDescription,
         RECURRENCE_EVENT_DURATION, updated_recurrence.eventDuration,
         RECURRENCE_TODO_NAME, updated_recurrence.todoName,
         RECURRENCE_TODO_TIMEFRAME, updated_recurrence.todoTimeframe,
         RECURRENCE_GOAL_NAME, updated_recurrence.goalName,
         RECURRENCE_GOAL_DESIRE_ID, updated_recurrence.goalDesireId,
         RECURRENCE_GOAL_HOW_MUCH, updated_recurrence.goalHowMuch,
         RECURRENCE_GOAL_MEASURING_UNITS, updated_recurrence.goalMeasuringUnits,
         RECURRENCE_GOAL_TIMEFRAME, updated_recurrence.goalTimeframe,
         recurrence_id))
    updated_recurrence.recurrenceId = cursor.lastrowid
    __generate_recurrence_instances_for_new_recurrence(authentication, updated_recurrence)
    return {"message": "recurrence successfully updated!"}


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
    delete_recurrence_instances_after_date(authentication, recurrence_id, end, False)

@router.delete("/api/calendar/recurrences/{recurrence_id}")
def delete_recurrence(authentication: Authentication, recurrence_id: int):
    get_recurrence(authentication, recurrence_id)  # authentication
    cursor.execute("DELETE FROM recurrences WHERE recurrence_id = %s", (recurrence_id,))
    return "recurrence successfully deleted"


@router.delete("/api/calendar/recurrences/{recurrence_id}")
def delete_recurrence_instances_after_date(authentication: Authentication, recurrence_id, after: float,
                                           inclusive: bool):
    get_recurrence(authentication, recurrence_id)  # authenticate
    cursor.execute("DELETE FROM goals WHERE recurrence_id = %s AND %s %s %s;",
                   (recurrence_id, RECURRENCE_DAY, ">=" if inclusive else ">", after))
    cursor.execute("DELETE FROM todos WHERE recurrence_id = %s AND %s %s %s;",
                   (recurrence_id, RECURRENCE_DAY, ">=" if inclusive else ">", after))
    cursor.execute("DELETE FROM events WHERE recurrence_id = %s AND %s %s %s",
                   (recurrence_id, RECURRENCE_DAY, ">=" if inclusive else ">", after))
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
        recurrence = Recurrence.from_sql_res(row.__dict__)
        rule = rrule.rrulestr(recurrence.rruleString)
        start_dt = datetime(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_dt = start_dt + relativedelta.relativedelta(months=1) - timedelta(minutes=1)
        if end_dt.timestamp() >= recurrence.startInstant:  # if within recurrence timeframe, generate instances, else pass
            occurrences = rule.between(after=start_dt, before=end_dt, inc=True)
            for occurrence in occurrences:
                if occurrence.timestamp() >= recurrence.startInstant:
                    event, todo, goal = recurrence.generate_instance_objects(occurrence)
                    if goal is not None:
                        goal_id = GoalAchievingEndpoints.create_goal(authentication, goal)
                        todo.linkedGoalId = goal_id
                        if event is not None:
                            event.linkedGoalId = goal_id
                    if todo is not None:
                        todo_id = CalendarToDoEndpoints.create_todo(authentication, todo)
                        event.linkedTodoId = todo_id
                    if event is not None:
                        CalendarEventEndpoints.create_calendar_event(authentication, event)

        # idea to make this faster:
        # add mass insert id to group bulk insert events, todos, and goals
        # then use mass insert id to easily fetch those ids and add it to the linkedGoalIds + linkedToDoIds


def __generate_recurrence_instances_for_new_recurrence(authentication: Authentication, recurrence: Recurrence):
    year_month_tuples = get_months_accessed_by_user(authentication.user_id)
    for year, month in year_month_tuples:
        rule = rrule.rrulestr(recurrence.rruleString)
        start_dt = datetime(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_dt = start_dt + relativedelta.relativedelta(months=1) - timedelta(minutes=1)
        if end_dt.timestamp() >= recurrence.startInstant:  # if within recurrence timeframe, generate instances, else pass
            occurrences = rule.between(after=start_dt, before=end_dt, inc=True)
            for occurrence in occurrences:
                if occurrence.timestamp() >= recurrence.startInstant:
                    event, todo, goal = recurrence.generate_instance_objects(occurrence)
                    if goal is not None:
                        goal_id = GoalAchievingEndpoints.create_goal(authentication, goal)
                        todo.linkedGoalId = goal_id
                        if event is not None:
                            event.linkedGoalId = goal_id
                    if todo is not None:
                        todo_id = CalendarToDoEndpoints.create_todo(authentication, todo)
                        event.linkedTodoId = todo_id
                    if event is not None:
                        CalendarEventEndpoints.create_calendar_event(authentication, event)


def get_end_instant_with_timeframe(timeframe: Recurrence.Timeframe, start_instant: float):
    # INDEFINITE timeframe todos do not appear in todos_in_day, as they are not bounded to any timeframe, but will simply disappear when they are completed
    if timeframe == Recurrence.Timeframe.INDEFINITE:
        return
    deadline: datetime
    if timeframe == Recurrence.Timeframe.DAY:
        deadline = datetime.fromtimestamp(start_instant) + timedelta(days=1)
    elif timeframe == Recurrence.Timeframe.WEEK:
        deadline = datetime.fromtimestamp(start_instant) + timedelta(days=7)
    elif timeframe == Recurrence.Timeframe.MONTH:
        deadline = datetime.fromtimestamp(start_instant) + relativedelta.relativedelta(months=1)
    else:  # timeframe == Recurrence.Timeframe.YEAR:
        deadline = datetime.fromtimestamp(start_instant) + relativedelta.relativedelta(years=1)
    return deadline.timestamp()


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


def __validate_recurrence(authentication: Authentication, recurrence: Recurrence):
    if recurrence.userId is None:
        raise HTTPException(detail="recurrence must define a user id", status_code=400)
    if recurrence.userId != authentication.user_id:
        raise HTTPException(detail="recurrence user id must match authentication user id", status_code=400)
    if recurrence.rruleString is None:
        raise HTTPException(detail="recurrence must define a valid rrule string", status_code=400)
    try:
        rrule.rrulestr(recurrence.rruleString)  # todo: check if this actually throws errors in case of invalid rrule strings
    except Exception:
        raise HTTPException(detail="recurrence rrule string is not valid", status_code=400)
    if recurrence.startInstant is None:
        raise HTTPException(detail="recurrence must define a valid starting instant", status_code=400)

    if recurrence.goalName is not None:
        if recurrence.todoName is None:
            raise HTTPException(detail="Todo must be created if a goal is defined", status_code=400)
        if recurrence.todoTimeframe != recurrence.goalTimeframe:
            raise HTTPException(detail="Todo and goal timeframes must be equivalent", status_code=400)

        if len(recurrence.goalName) == 0 or len(recurrence.goalName) > 42:
            raise HTTPException(detail="goal name must be between 1 and 42 characters", status_code=400)
        if recurrence.goalDesireId is None:
            raise HTTPException(detail="goal must define a desire to be linked with", status_code=400)
        # authenticate desire id
        GoalAchievingEndpoints.get_desire(authentication, recurrence.goalDesireId)
        if recurrence.goalHowMuch is None:
            raise HTTPException(detail="goal must define a quantity to achieve", status_code=400)
        if recurrence.goalHowMuch <= 0:
            raise HTTPException(detail="goal must define a quantity greater than 0 to achieve", status_code=400)
        if recurrence.goalMeasuringUnits is not None:
            if len(recurrence.goalMeasuringUnits) > 12 or len(recurrence.goalMeasuringUnits) == 0:
                raise HTTPException(detail="goal measuring units must be between 1 and 12 characters in length", status_code=400)
    if recurrence.eventName is not None:
        if len(recurrence.eventName) == 0 or len(recurrence.eventName) > 32:
            raise HTTPException(detail="goal name must be between 1 and 32 characters long", status_code=400)
        if recurrence.eventDuration is None:
            raise HTTPException(detail="event must define a valid duration", status_code=400)
        if recurrence.eventDuration <= 0:
            raise HTTPException(detail="event must define a valid duration greater than 0", status_code=400)
        if recurrence.eventDescription is None:
            raise HTTPException(detail="event must define a valid description", status_code=400)
        if len(recurrence.eventDescription) == 0 or len(recurrence.eventDescription) > 500:
            raise HTTPException(detail="event description must be between 1 and 500 characters in length", status_code=400)

    if recurrence.eventName is None and recurrence.goalName is None and recurrence.todoName is None:
        raise HTTPException(detail="recurrence must define a goal, todo, and/or event to repeat", status_code=400)
