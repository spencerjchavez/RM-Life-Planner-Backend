from typing import Optional

from fastapi import APIRouter, HTTPException
from mysql.connector import MySQLConnection
from mysql.connector.cursor_cext import CMySQLCursorDict
from app.extras.SQLDateValidator import *

from app.models.Authentication import Authentication
from app.extras.SQLColumnNames import *
from datetime import datetime, timedelta
from dateutil import relativedelta
from app.models.Recurrence import Recurrence
from dateutil import rrule
from dateutil.rrule import rrulestr
from app.endpoints import GoalAchievingEndpoints, CalendarToDoEndpoints, CalendarEventEndpoints, UserEndpoints

router = APIRouter()
db: MySQLConnection
cursor: CMySQLCursorDict

months_accessed_cache: {int: {int: {int: bool}}} = {}  # user_id, year, month, if month has been accessed


@router.post("/api/calendar/recurrences")
def create_recurrence(authentication: Authentication, recurrence: Recurrence):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
    __validate_recurrence(authentication, recurrence)
    q = recurrence.get_sql_insert_query()
    params = recurrence.get_sql_insert_params()
    cursor.execute(q, params)
    recurrence.recurrenceId = cursor.lastrowid
    
    __generate_recurrence_instances_for_new_recurrence(authentication, recurrence)
    
    return {"recurrence_id": recurrence.recurrenceId}


@router.get("/api/calendar/recurrences/{recurrence_id}")
def get_recurrence(auth_user: int, api_key: str, recurrence_id: int):
    authentication = Authentication(auth_user, api_key)
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
    cursor.execute("SELECT * FROM recurrences WHERE recurrence_id = %s", (recurrence_id,))
    res = cursor.fetchone()
    if res is None:
        raise HTTPException(detail="specified recurrence does not exist", status_code=404)
    if res["user_id"] != authentication.user_id:
        raise HTTPException(status_code=401, detail="User is not authenticated to access this resource")
    recurrence = Recurrence.from_sql_res(res)
    return {"recurrence": recurrence}


@router.put("/api/calendar/recurrences/put/{recurrence_id}")
def update_recurrence(authentication: Authentication, recurrence_id: int, updated_recurrence: Recurrence,
                      after: Optional[str] = None,
                      inclusive: Optional[bool] = True):
    # authenticate
    _ = get_recurrence(authentication.user_id, authentication.api_key, recurrence_id)
    updated_recurrence.recurrenceId = recurrence_id
    if after is None:
        after = updated_recurrence.startDate
        inclusive = True
    updated_recurrence.startDate = after
    __validate_recurrence(authentication, updated_recurrence)
    delete_recurrence_instances_after_date(authentication.user_id, authentication.api_key, recurrence_id, after, inclusive)

    # insert new recurrence
    cursor.execute(
        f"UPDATE recurrences SET {START_DATE} = %s, "
        f"{START_TIME} = %s, {RRULE_STRING} = %s, "
        f"{RECURRENCE_EVENT_NAME} = %s, "
        f"{RECURRENCE_EVENT_DESCRIPTION} = %s, "
        f"{RECURRENCE_EVENT_DURATION}= %s, "
        f"{RECURRENCE_TODO_NAME} = %s, "
        f"{RECURRENCE_TODO_TIMEFRAME} = %s, "
        f"todo_how_much_planned = %s, "
        f"{RECURRENCE_GOAL_NAME} = %s, "
        f"{RECURRENCE_GOAL_DESIRE_ID} = %s, "
        f"{RECURRENCE_GOAL_HOW_MUCH} = %s, "
        f"{RECURRENCE_GOAL_MEASURING_UNITS} = %s, "
        f"{RECURRENCE_GOAL_TIMEFRAME} = %s WHERE recurrence_id = %s",
        (updated_recurrence.startDate,
         updated_recurrence.startTime,
         updated_recurrence.rruleString,
         updated_recurrence.eventName,
         updated_recurrence.eventDescription,
         updated_recurrence.eventDuration,
         updated_recurrence.todoName,
         updated_recurrence.todoTimeframe,
         updated_recurrence.todoHowMuchPlanned,
         updated_recurrence.goalName,
         updated_recurrence.goalDesireId,
         updated_recurrence.goalHowMuch,
         updated_recurrence.goalMeasuringUnits,
         updated_recurrence.goalTimeframe,
         recurrence_id))
    
    __generate_recurrence_instances_for_new_recurrence(authentication, updated_recurrence)
    
    return {"message": "recurrence successfully updated!"}


# TODO: allow extending the end also. decide how we wanna handle updating recurrence instances that have been altered/etc
@router.put("/api/calendar/recurrences/put-dtend/{recurrence_id}")
def set_recurrence_end(authentication: Authentication, recurrence_id: int, end: str):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
    if not validate_date(end):
        raise HTTPException(detail="invalid after date parameter format", status_code=400)
    cursor.execute("SELECT * FROM recurrences WHERE recurrence_id = %s", (recurrence_id,))
    res = cursor.fetchone()
    if res["user_id"] != authentication.user_id:
        raise HTTPException(status_code=401, detail="User is not authenticated to modify this resource")
    rule = rrulestr(res[RRULE_STRING])
    rule = rule.replace(until=datetime.strptime(end, "%Y-%m-%d"))
    cursor.execute(f"UPDATE recurrences SET {RRULE_STRING} = %s WHERE recurrence_id = %s",
                   (str(rule), recurrence_id))
    delete_recurrence_instances_after_date(authentication, recurrence_id, end, False)
    
    return {"message": "successfully updated"}


@router.delete("/api/calendar/recurrences/{recurrence_id}")
def delete_recurrence(auth_user: int, api_key: str, recurrence_id: int):
    get_recurrence(auth_user, api_key, recurrence_id)  # authentication
    cursor.execute("DELETE FROM events WHERE recurrence_id = %s", (recurrence_id,))
    cursor.execute("DELETE FROM todos WHERE recurrence_id = %s", (recurrence_id,))
    cursor.execute("DELETE FROM goals WHERE recurrence_id = %s", (recurrence_id,))
    cursor.execute("DELETE FROM recurrences WHERE recurrence_id = %s", (recurrence_id,))
    
    return "recurrence successfully deleted"


#@router.delete("/api/calendar/recurrences/{recurrence_id}/after/{after}")
def delete_recurrence_instances_after_date(auth_user: int, api_key: str, recurrence_id, after: str,
                                           inclusive: bool):
    get_recurrence(auth_user, api_key, recurrence_id)  # authenticate
    if not validate_date(after):
        raise HTTPException(detail="invalid after date parameter format", status_code=400)
    greater_than_inclusive = ">=" if inclusive else ">"
    cursor.execute(f"DELETE FROM events WHERE recurrence_id = %s AND {RECURRENCE_DATE} {greater_than_inclusive} %s",
                   (recurrence_id, after))
    cursor.execute(f"DELETE FROM todos WHERE recurrence_id = %s AND {RECURRENCE_DATE} {greater_than_inclusive} %s;",
                   (recurrence_id, after))
    cursor.execute(f"DELETE FROM goals WHERE recurrence_id = %s AND {RECURRENCE_DATE} {greater_than_inclusive} %s;",
                   (recurrence_id, after))
    

#
#
# generate instances of rrule
#
#

def __generate_recurrence_instances_for_month(authentication: Authentication, year: int, month: int):
    cursor.execute("SELECT * FROM recurrences WHERE user_id = %s", (authentication.user_id,))
    res = cursor.fetchall()
    for row in res:
        recurrence = Recurrence.from_sql_res(row)
        rule = rrule.rrulestr(recurrence.rruleString, dtstart=datetime.strptime(recurrence.startDate, "%Y-%m-%d"))
        start_dt = datetime(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_dt = start_dt + relativedelta.relativedelta(months=1) - timedelta(minutes=1)
        if end_dt >= datetime.strptime(recurrence.startDate, "%Y-%m-%d"):  # if within recurrence timeframe, generate instances, else pass
            occurrences = rule.between(after=start_dt, before=end_dt, inc=True)
            for occurrence in occurrences:
                if occurrence >= datetime.strptime(recurrence.startDate, "%Y-%m-%d"):
                    event, todo, goal = recurrence.generate_instance_objects_on_date(occurrence)
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
    db.autocommit = False
    for year, month in year_month_tuples:
        rule = rrule.rrulestr(recurrence.rruleString, dtstart=datetime.strptime(recurrence.startDate, "%Y-%m-%d"))
        start_dt = datetime(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_dt = start_dt + relativedelta.relativedelta(months=1) - timedelta(minutes=1)
        if end_dt >= datetime.strptime(recurrence.startDate, "%Y-%m-%d"):  # if within recurrence timeframe, generate instances, else pass
            occurrences = rule.between(after=start_dt, before=end_dt, inc=True)
            for occurrence in occurrences:
                if occurrence >= datetime.strptime(recurrence.startDate, "%Y-%m-%d"):
                    event, todo, goal = recurrence.generate_instance_objects_on_date(occurrence)
                    if goal is not None:
                        goal_id = GoalAchievingEndpoints.create_goal(authentication, goal)["goal_id"]
                        todo.linkedGoalId = goal_id
                        if event is not None:
                            event.linkedGoalId = goal_id
                    if todo is not None:
                        todo_id = CalendarToDoEndpoints.create_todo(authentication, todo)["todo_id"]
                        if event is not None:
                            event.linkedTodoId = todo_id
                    if event is not None:
                        CalendarEventEndpoints.create_calendar_event(authentication, event)
    db.commit()
    db.autocommit = True


def get_end_instant_with_timeframe(timeframe: Recurrence.Timeframe, start_datetime: datetime):
    # INDEFINITE timeframe todos do not appear in todos_in_day, as they are not bounded to any timeframe, but will simply disappear when they are completed
    if timeframe == Recurrence.Timeframe.INDEFINITE:
        return
    deadline: datetime
    if timeframe == Recurrence.Timeframe.DAY:
        deadline = start_datetime + timedelta(days=1)
    elif timeframe == Recurrence.Timeframe.WEEK:
        deadline = start_datetime + timedelta(days=7)
    elif timeframe == Recurrence.Timeframe.MONTH:
        deadline = start_datetime + relativedelta.relativedelta(months=1)
    else:  # timeframe == Recurrence.Timeframe.YEAR:
        deadline = start_datetime + relativedelta.relativedelta(years=1)
    return deadline.timestamp()


#
#
# months accessed tracking stuff
#
#
def get_months_accessed_by_user(user_id):
    cursor.execute("SELECT month, year FROM months_accessed_by_user WHERE user_id = %s",
                   (user_id,))
    res = cursor.fetchall()
    year_month_tuples = []
    for row in res:
        year = row["year"]
        month = row["month"]
        year_month_tuples.append((year, month))
        months_accessed_cache.setdefault(user_id, {}).setdefault(year, {})[month] = True
    return year_month_tuples


def register_month_accessed_by_user(authentication: Authentication, year: int, month: int):
    if not months_accessed_cache.get(authentication.user_id, {}).get(year, {}).get(month, False):
        cursor.execute(
            "SELECT * FROM months_accessed_by_user WHERE user_id = %s AND year = %s AND month = %s;",
            (authentication.user_id, year, month))
        if cursor.fetchone() is None:  # month has not been accessed before
            cursor.execute("INSERT INTO months_accessed_by_user VALUES (%s, %s, %s)",
                           (authentication.user_id, year, month))
            
            #_ = cursor.fetchone()  # for some weird reason this is necessary to actually execute the insert
        months_accessed_cache.setdefault(authentication.user_id, {}).setdefault(year, {})[
            month] = True
        __generate_recurrence_instances_for_month(authentication, year, month)


def __validate_recurrence(authentication: Authentication, recurrence: Recurrence):
    if recurrence.userId is None:
        raise HTTPException(detail="recurrence must define a user id", status_code=400)
    if recurrence.userId != authentication.user_id:
        raise HTTPException(detail="recurrence user id must match authentication user id", status_code=401)
    if recurrence.rruleString is None:
        raise HTTPException(detail="recurrence must define a valid rrule string", status_code=400)
    try:
        rule = rrule.rrulestr(recurrence.rruleString)  # todo: check if this actually throws errors in case of invalid rrule strings
        if recurrence.todoTimeframe is not None:
            if rule._freq == 3:
                if recurrence.todoTimeframe != Recurrence.Timeframe.DAY:
                    raise HTTPException(detail="timeframe must match the timeframe set in the rrule string", status_code=400)
            if rule._freq == 2:
                if recurrence.todoTimeframe != Recurrence.Timeframe.WEEK:
                    raise HTTPException(detail="timeframe must match the timeframe set in the rrule string", status_code=400)
            if rule._freq == 1:
                if recurrence.todoTimeframe != Recurrence.Timeframe.MONTH:
                    raise HTTPException(detail="timeframe must match the timeframe set in the rrule string", status_code=400)
            if rule._freq == 0:
                if recurrence.todoTimeframe != Recurrence.Timeframe.YEAR:
                    raise HTTPException(detail="timeframe must match the timeframe set in the rrule string", status_code=400)
    except Exception:
        raise HTTPException(detail="recurrence rrule string is not valid", status_code=400)
    if recurrence.startDate is None:
        raise HTTPException(detail="recurrence must define a valid starting date", status_code=400)
    if not validate_date(recurrence.startDate):
        raise HTTPException(detail="recurrence has an invalid starting date", status_code=400)
    if recurrence.startTime is None:
        raise HTTPException(detail="recurrence must define a valid starting time", status_code=400)
    if not validate_time(recurrence.startTime):
        raise HTTPException(detail="recurrence has an invalid starting time", status_code=400)

    if recurrence.goalName is not None:
        if recurrence.todoName is None:
            raise HTTPException(detail="Todo must be created if a goal is defined", status_code=400)
        if recurrence.todoTimeframe != recurrence.goalTimeframe or recurrence.todoTimeframe is None:
            raise HTTPException(detail="Todo and goal timeframes must be valid and equivalent", status_code=400)
        if recurrence.todoHowMuchPlanned != recurrence.goalHowMuch:
            raise HTTPException(detail="Todo and goal how much parameters must be equivalent", status_code=400)
        if len(recurrence.goalName) == 0 or len(recurrence.goalName) > 42:
            raise HTTPException(detail="goal name must be between 1 and 42 characters", status_code=400)
        if recurrence.goalDesireId is None:
            raise HTTPException(detail="goal must define a desire to be linked with", status_code=400)
        # authenticate desire id
        GoalAchievingEndpoints.get_desire(authentication.user_id, authentication. api_key, recurrence.goalDesireId)
        if recurrence.goalHowMuch is None:
            raise HTTPException(detail="goal must define a quantity to achieve", status_code=400)
        if recurrence.goalHowMuch <= 0:
            raise HTTPException(detail="goal must define a quantity greater than 0 to achieve", status_code=400)
        if recurrence.goalMeasuringUnits is not None:
            if len(recurrence.goalMeasuringUnits) > 12 or len(recurrence.goalMeasuringUnits) == 0:
                raise HTTPException(detail="goal measuring units must be between 1 and 12 characters in length", status_code=400)
    if recurrence.todoName is not None:
        if recurrence.todoTimeframe is None:
            raise HTTPException(detail="todo must define a valid timeframe", status_code=400)
        if recurrence.todoHowMuchPlanned is None:
            raise HTTPException(detail="todo must define a valid how much planned attribute", status_code=400)
        if recurrence.todoHowMuchPlanned <= 0:
            raise HTTPException(detail="todo must define a how much planned attribute greater than 0", status_code=400)
    if recurrence.eventName is not None:
        if len(recurrence.eventName) == 0 or len(recurrence.eventName) > 32:
            raise HTTPException(detail="goal name must be between 1 and 32 characters long", status_code=400)
        if recurrence.eventDuration is None:
            raise HTTPException(detail="event must define a valid duration", status_code=400)
        if recurrence.eventDuration <= 0:
            raise HTTPException(detail="event must define a valid duration greater than 0", status_code=400)
        if recurrence.eventDescription is not None:
            if len(recurrence.eventDescription) > 500:
                raise HTTPException(detail="event description must be less than 500 characters in length", status_code=400)
    if recurrence.eventName is None and recurrence.goalName is None and recurrence.todoName is None:
        raise HTTPException(detail="recurrence must define a goal, todo, and/or event to repeat", status_code=400)
