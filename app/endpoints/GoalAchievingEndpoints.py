# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from typing import Optional

import mysql.connector.errors
from mysql.connector.pooling import PooledMySQLConnection
from app.db_connections import DBConnections
from app.extras.SQLDateValidator import *
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, HTTPException
from mysql.connector.cursor_cext import CMySQLCursorDict

from app.models.Desire import Desire
from app.models.Goal import Goal
from app.models.Authentication import Authentication
from app.extras.SQLColumnNames import *
from app.endpoints import RecurrenceEndpoints, UserEndpoints

desires_url = "/api/desires"
goals_url = "/api/goals"
plans_url = "/api/plans"
actions_url = "/api/actions"

desires_per_user_limit = 50
desire_categories_per_user_limit = 10
goals_per_desire_limit = 20

router = APIRouter()


# DESIRE ENDPOINTS
@router.post("/api/desires")
def create_desire(authentication: Authentication, desire: Desire):
    conn: PooledMySQLConnection = DBConnections.get_db_connection()
    cursor: CMySQLCursorDict = conn.cursor(dictionary=True)
    try:
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        desire.dateCreated = datetime.now().strftime("%Y-%m-%d")
        __validate_desire(authentication, desire)
        query = desire.get_sql_insert_query()
        params = desire.get_sql_insert_params()
        cursor.execute(query, params)

        return {"desire_id": cursor.lastrowid}
    finally:
        conn.close()


@router.get("/api/desires/{desire_id}")
def get_desire(auth_user: int, api_key: str, desire_id: int):
    conn: PooledMySQLConnection = DBConnections.get_db_connection()
    cursor: CMySQLCursorDict = conn.cursor(dictionary=True)
    try:
        authentication = Authentication(auth_user, api_key)
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        cursor.execute("SELECT * FROM desires WHERE desire_id = %s", (desire_id,))
        res = cursor.fetchone()
        if res is None:
            raise HTTPException(detail="no such desire exists", status_code=404)
        if res["user_id"] != user_id:
            raise HTTPException(detail="User is not authenticated to access this resource", status_code=401)
        return {"desire": Desire.from_sql_res(res)}
    finally:
        conn.close()

@router.get("/api/desires/by-user-id/{user_id}")
def get_desires_by_user_id(auth_user: int, api_key: str, user_id: int):
    conn: PooledMySQLConnection = DBConnections.get_db_connection()
    cursor: CMySQLCursorDict = conn.cursor(dictionary=True)
    try:
        user_id = auth_user
        if not UserEndpoints.authenticate(Authentication(auth_user, api_key)):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        cursor.execute("SELECT * FROM desires WHERE user_id=%s AND date_retired IS NULL", (user_id,))
        desires = []
        for desire in cursor.fetchall():
            desires.append(Desire.from_sql_res(desire))
        return {"desires": desires}
    finally:
        conn.close()


@router.put("/api/desires/{desire_id}")
def update_desire(authentication: Authentication, desire_id: int, updated_desire: Desire):
    conn: PooledMySQLConnection = DBConnections.get_db_connection()
    cursor: CMySQLCursorDict = conn.cursor(dictionary=True)
    try:
        get_desire(authentication.user_id, authentication.api_key, desire_id)
        updated_desire.desireId = desire_id
        __validate_desire(authentication, updated_desire)
        query = f"UPDATE desires SET {NAME} = %s, {DEADLINE} = %s, {DATE_RETIRED} = %s WHERE desire_id = %s"
        params = (updated_desire.name, updated_desire.deadline, updated_desire.dateRetired, desire_id)
        cursor.execute(query, params)
        return {"message": f"Desire with ID {desire_id} updated successfully"}
    finally:
        conn.close()


@router.delete("/api/desires/{desire_id}")
def delete_desire(auth_user: int, api_key: str, desire_id: int):
    conn: PooledMySQLConnection = DBConnections.get_db_connection()
    cursor: CMySQLCursorDict = conn.cursor(dictionary=True)
    try:
        authentication = Authentication(auth_user, api_key)
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        cursor.execute("SELECT * FROM desires WHERE desire_id = %s", (desire_id,))
        res = cursor.fetchone()
        if res is None:
            raise HTTPException(status_code=404, detail="Desire not found")
        if res["user_id"] != user_id:
            raise HTTPException(detail="User is not authorized to access this resource", status_code=401)

        cursor.execute("DELETE FROM desires WHERE desire_id = %s", (desire_id,))

        return {"message": f"Desire with ID {desire_id} deleted successfully"}
    except mysql.connector.errors.IntegrityError as _:
        raise HTTPException(detail="Cannot delete desire until all of its linked goals are deleted", status_code=400)
    finally:
        conn.close()



def __validate_desire(authentication: Authentication, desire: Desire):
    if desire.userId is None:
        raise HTTPException(detail="desire missing userId", status_code=400)
    if authentication.user_id != desire.userId:
        raise HTTPException(detail="User is not authenticated to create this resource", status_code=401)
    if desire.name is None:
        desire.name = ""
        #raise HTTPException(detail="desire missing a name", status_code=400)
    elif len(desire.name) == 0:
        pass
        #raise HTTPException(detail="desire missing a name", status_code=400)
    elif len(desire.name) > 42:
        raise HTTPException(detail="desire name must not exceed 42 characters", status_code=400)
    if desire.dateCreated is None:
        raise HTTPException(detail="desire missing a creation date", status_code=400)
    """if desire.colorR is None or desire.colorG is None or desire.colorB is None:
        raise HTTPException(detail="desire missing color", status_code=400)
    if desire.colorR < 0 or desire.colorR > 1 \
            or desire.colorB < 0 or desire.colorB > 1 \
            or desire.colorG < 0 or desire.colorG > 1:
        raise HTTPException(detail="desire does not define a valid color", status_code=400)"""


#
#
# GOALS ENDPOINTS
#
#

@router.post("/api/goals")
def create_goal(authentication: Authentication, goal: Goal):
    conn: PooledMySQLConnection = DBConnections.get_db_connection()
    cursor: CMySQLCursorDict = conn.cursor(dictionary=True)
    try:
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        __validate_goal(authentication, goal)
        stmt = goal.get_sql_insert_query()
        params = goal.get_sql_insert_params()
        cursor.execute(stmt, params)
        goal.goalId = cursor.lastrowid
        return {"goal_id": goal.goalId}
    finally:
        conn.close()

@router.get("/api/goals/by-goal-id/{goal_id}")
def get_goal(auth_user: int, api_key: str, goal_id: int):
    conn: PooledMySQLConnection = DBConnections.get_db_connection()
    cursor: CMySQLCursorDict = conn.cursor(dictionary=True)
    try:
        authentication = Authentication(auth_user, api_key)
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        cursor.execute("SELECT * FROM goals WHERE goal_id = %s", (goal_id,))
        res = cursor.fetchone()
        if res is None:
            raise HTTPException(detail="No goal of specified id found", status_code=404)
        if res["user_id"] != user_id:
            raise HTTPException(detail="User is not authorized to access this resource", status_code=401)
        return {"goal": Goal.from_sql_res(res)}
    finally:
        conn.close()


@router.post("/api/goals/by-goal-id")
def get_goals(auth_user: int, api_key: str, goal_ids: list[int]):
    conn: PooledMySQLConnection = DBConnections.get_db_connection()
    cursor: CMySQLCursorDict = conn.cursor(dictionary=True)
    try:
        if not UserEndpoints.authenticate(Authentication(auth_user, api_key)):
            raise HTTPException(status_code=401, detail="User not authenticated, please log in")
        in_clause = "("
        in_params = ()
        for goal_id in goal_ids:
            in_clause += "%s,"
            in_params += (goal_id,)
        in_clause = in_clause[:len(in_clause)-1] + ")"
        cursor.execute("SELECT * FROM goals WHERE goal_id IN " + in_clause, in_params)
        to_return = []
        res = cursor.fetchall()
        for row in res:
            if row["user_id"] != auth_user:
                raise HTTPException(status_code=401, detail="User not authorized to access this resource")
            to_return.append(Goal.from_sql_res(row))
        return {"goals": to_return}
    finally:
        conn.close()


@router.get("/api/goals/in-date-range")
def get_goals_in_date_range(auth_user: int, api_key: str, start_date: str, end_date: Optional[str] = None, desire_id: Optional[int] = None):
    conn: PooledMySQLConnection = DBConnections.get_db_connection()
    cursor: CMySQLCursorDict = conn.cursor(dictionary=True)
    try:
        if desire_id is not None:
            _ = get_desire(auth_user, api_key, desire_id)
        authentication = Authentication(auth_user, api_key)
        if end_date is None:
            end_date = start_date
        if not validate_date(start_date) or not validate_date(end_date):
            raise HTTPException(detail="invalid date provided!", status_code=400)
        dt = datetime.strptime(start_date, "%Y-%m-%d")
        dt_end = datetime.strptime(end_date, "%Y-%m-%d")
        if dt_end < dt:
            raise HTTPException(detail="end date cannot be before start date", status_code=400)
        year_months = set()
        while dt <= dt_end:
            year_months.add((dt.year, dt.month))
            dt += relativedelta(months=1)

        for year, month in year_months:
            # register what months we are accessing to generate recurrence events
            RecurrenceEndpoints.register_month_accessed_by_user(authentication, year, month)

        if desire_id is None:
            cursor.execute("SELECT * FROM goals WHERE user_id = %s AND deadline_date >= %s AND start_date <= %s"
                           "UNION "
                           "SELECT * FROM goals WHERE user_id = %s AND start_date <= %s AND deadline_date IS NULL",
                           (authentication.user_id, start_date, end_date, authentication.user_id, end_date))
        else:
            cursor.execute("SELECT * FROM goals WHERE user_id = %s AND desire_id = %s AND deadline_date >= %s AND start_date <= %s"
                           "UNION "
                           "SELECT * FROM goals WHERE user_id = %s AND desire_id = %s AND start_date <= %s AND deadline_date IS NULL",
                           (authentication.user_id, desire_id, start_date, end_date, authentication.user_id, desire_id, end_date))
        goals = []
        res = cursor.fetchall()
        for row in res:
            goals.append(Goal.from_sql_res(row))
        return {"goals": goals}
    finally:
        conn.close()


@router.post("/api/goals/in-date-list")
def get_goals_in_date_list(auth_user: int, api_key: str, dates: list[str], desire_id: Optional[int] = None):
    conn: PooledMySQLConnection = DBConnections.get_db_connection()
    cursor: CMySQLCursorDict = conn.cursor(dictionary=True)
    try:
        if desire_id:
            # authenticate user to desire_id
            _ = get_desire(auth_user, api_key, desire_id)
        authentication = Authentication(auth_user, api_key)
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
        year_months = set()
        for date_str in dates:
            if not validate_date(date_str):
                raise HTTPException(detail="invalid date provided!", status_code=400)
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            year_months.add((dt.year, dt.month))

        for year, month in year_months:
            # register what months we are accessing to generate recurrence events
            RecurrenceEndpoints.register_month_accessed_by_user(authentication, year, month)

        goals_by_day = {}
        for date_str in dates:
            if desire_id is None:
                cursor.execute("SELECT * FROM goals WHERE user_id = %s AND deadline_date >= %s AND start_date <= %s"
                               "UNION "
                               "SELECT * FROM goals WHERE user_id = %s AND start_date <= %s AND deadline_date IS NULL",
                               (authentication.user_id, date_str, date_str, authentication.user_id, date_str))
            else:
                cursor.execute("SELECT * FROM goals WHERE user_id = %s AND desire_id = %s AND deadline_date >= %s AND start_date <= %s"
                               "UNION "
                               "SELECT * FROM goals WHERE user_id = %s AND desire_id = %s AND start_date <= %s AND deadline_date IS NULL",
                               (authentication.user_id, desire_id, date_str, date_str, authentication.user_id, desire_id, date_str))
            goals_by_day[date_str] = []
            res = cursor.fetchall()
            for row in res:
                goals_by_day[date_str].append(Goal.from_sql_res(row))
        return {"goals": goals_by_day}
    finally:
        conn.close()


'''
@router.get("/api/calendar/goals/active/{user_id}/{day}")
def get_active_goals_on_date(authentication: Authentication, user_id: int, date: str):
    # returns all goals that start before the given date, end after the given date, and have not been completed
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="user is not authenticated, please log in", status_code=401)
    if authentication.user_id != user_id:
        raise HTTPException(detail="user not authorized to access this resource", status_code=401)
    cursor.execute("SELECT * FROM goals WHERE user_id = %s AND start_date < %s AND end_date > %s", (user_id, date, date))
    res = cursor.fetchall()
    goal_id_in_clause = "("
    for row in res:
        goal_id_in_clause += row["goal_id"] + ","
    goal_id_in_clause = goal_id_in_clause[:len(goal_id_in_clause) - 1]
    goal_id_in_clause += ")"
    # filter out goals which have been completed
    cursor.execute("SELECT how_much_accomplished, linked_goal_id FROM events WHERE linked_goal_id IN %s", (goal_id_in_clause,))
    goals_res = cursor.fetchall()

    res = cursor.fetchall()
    goals = []
    for row in res:
        goals.append(Goal.from_sql_res(row))
    return {"goals": goals}
'''


@router.put("/api/goals/{goal_id}")
def update_goal(authentication: Authentication, goal_id: int, updated_goal: Goal):
    conn: PooledMySQLConnection = DBConnections.get_db_connection()
    cursor: CMySQLCursorDict = conn.cursor(dictionary=True)
    try:
        goal = get_goal(authentication.user_id, authentication.api_key, goal_id)["goal"]
        updated_goal.goalId = goal_id
        __validate_goal(authentication, updated_goal)
        cursor.execute(
            "UPDATE goals SET desire_id = %s, name = %s, how_much = %s, measuring_units = %s, start_date = %s, deadline_date = %s WHERE goal_id = %s",
            (updated_goal.desireId, updated_goal.name, updated_goal.howMuch, updated_goal.measuringUnits,
             updated_goal.startDate, updated_goal.deadlineDate, goal_id))

        return {"message": f"Goal with ID {goal_id} updated successfully"}
    finally:
        conn.close()


@router.delete("/api/goals/{goal_id}")
def delete_goal(auth_user: int, api_key: str, goal_id: int):
    conn: PooledMySQLConnection = DBConnections.get_db_connection()
    cursor: CMySQLCursorDict = conn.cursor(dictionary=True)
    try:
        get_goal(auth_user, api_key, goal_id)
        cursor.execute("DELETE FROM goals WHERE goal_id = %s", (goal_id,))
        return {"message": f"Goal with ID {goal_id} deleted successfully"}
    except mysql.connector.errors.IntegrityError as _:
        raise HTTPException(detail="Cannot delete goal until all of its linked events and todos are deleted", status_code=400)
    finally:
        conn.close()


def __validate_goal(authentication: Authentication, goal: Goal):
    if goal.userId is None:
        raise HTTPException(detail="goal missing userId", status_code=400)
    if authentication.user_id != goal.userId:
        raise HTTPException(detail="User is not authenticated to create this resource", status_code=401)
    if goal.name is None:
        goal.name = ""
        #raise HTTPException(detail="goal missing a name", status_code=400)
    elif len(goal.name) == 0:
        pass
        #raise HTTPException(detail="goal missing a name", status_code=400)
    elif len(goal.name) > 42:
        raise HTTPException(detail="goal name must not exceed 42 characters", status_code=400)
    if goal.howMuch is None:
        raise HTTPException(detail="goal missing how much attribute", status_code=400)
    elif goal.howMuch <= 0:
        raise HTTPException(detail="how much attribute must be greater than 0", status_code=400)
    if goal.measuringUnits is not None:
        if len(goal.measuringUnits) > 12:
            raise HTTPException(detail="measuring units cannot exceed 12 characters", status_code=400)
    if goal.startDate is None:
        raise HTTPException(detail="goal missing start date", status_code=400)
    if goal.priorityLevel is None:
        raise HTTPException(detail="goal must indicate a priority level", status_code=400)
    if goal.priorityLevel <= 0 or goal.priorityLevel > 5:
        raise HTTPException(detail="goal priority level must be in range 1 - 5", status_code=400)
    try:
        start_dt = datetime.strptime(goal.startDate, "%Y-%m-%d")
        if goal.deadlineDate is not None:
            deadline_dt = datetime.strptime(goal.deadlineDate, "%Y-%m-%d")
            if deadline_dt < start_dt:
                raise HTTPException(detail="goal's end instant cannot be less than its start instant", status_code=400)
        if goal.recurrenceDate is not None:
            _ = datetime.strptime(goal.recurrenceDate, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(detail="goal has improper date properties!", status_code=400)
    if goal.desireId is None:
        raise HTTPException(detail="goal missing a linked desire", status_code=400)
    # check authentication on desireId
    desire = get_desire(authentication.user_id, authentication.api_key, goal.desireId)["desire"]
    if desire.dateRetired is not None:  # desire is no longer active
        raise HTTPException(
            detail="linked desire is no longer active. Reactivate it or create a different desire to use.",
            status_code=400)
    if (goal.recurrenceId is not None and goal.recurrenceDate is None) or \
            (goal.recurrenceId is None and goal.recurrenceDate is not None):
        raise HTTPException(detail="recurrenceId and recurrenceDay must either both be defined, or neither defined",
                            status_code=400)
    # check authentication on recurrenceId
    if goal.recurrenceId is not None:
        RecurrenceEndpoints.get_recurrence(authentication.user_id, authentication.api_key, goal.recurrenceId)
