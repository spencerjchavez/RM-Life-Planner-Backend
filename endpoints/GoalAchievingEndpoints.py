# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from datetime import datetime, timedelta
from typing import Optional, Annotated

from fastapi import APIRouter, HTTPException, Query
from mysql.connector.cursor_cext import CMySQLCursorDict

from models.Desire import Desire
from models.Plan import Plan
from models.Goal import Goal
from endpoints import UserEndpoints, CalendarEventEndpoints
from models.Authentication import Authentication
from models.SQLColumnNames import *
import time
from endpoints import RecurrenceEndpoints

desires_url = "/api/desires"
goals_url = "/api/goals"
plans_url = "/api/plans"
actions_url = "/api/actions"

desires_per_user_limit = 50
desire_categories_per_user_limit = 10
goals_per_desire_limit = 20

router = APIRouter()
cursor: CMySQLCursorDict


# DESIRE ENDPOINTS
@router.post("/api/desires")
def create_desire(authentication: Authentication, desire: Desire):
    user_id = authentication.user_id
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    desire.dateCreated = time.time()
    __validate_desire(authentication, desire)
    query = desire.get_sql_insert_query()
    params = desire.get_sql_insert_params()
    cursor.execute(query, params)
    return {"message": "Desire created successfully", "desire_id": cursor.lastrowid}


@router.get("/api/desires/{desire_id}")
def get_desire(authentication: Authentication, desire_id: int):
    user_id = authentication.user_id
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    cursor.execute("SELECT * FROM desires WHERE desire_id = %s", (desire_id,))
    res = cursor.fetchone()
    if res is None:
        raise HTTPException(detail="no such desire exists", status_code=404)
    if res["user_id"] != user_id:
        raise HTTPException(detail="User is not authenticated to access this resource", status_code=401)
    return {"message": "successfully got desire", "desire": Desire.from_sql_res(res)}


@router.put("/api/desires/{desire_id}")
def update_desire(authentication: Authentication, desire_id: int, updated_desire: Desire):
    get_desire(authentication, desire_id)
    updated_desire.desireId = desire_id
    __validate_desire(authentication, updated_desire)
    query = f"UPDATE desires SET {NAME} = %s, {DEADLINE} = %s, {DATE_RETIRED} = %s, {PRIORITY_LEVEL} = %s,  {COLOR_R} = %s, {COLOR_G} = %s, {COLOR_B} = %s WHERE desire_id = %s"
    params = (updated_desire.name, updated_desire.deadline, updated_desire.dateRetired, updated_desire.priorityLevel,
              updated_desire.colorR, updated_desire.colorG, updated_desire.colorB, desire_id)
    cursor.execute(query, params)
    return f"Desire with ID {desire_id} updated successfully"


@router.delete("/api/desires/{desire_id}")
def delete_desire(authentication: Authentication, desire_id: int):
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
    _ = cursor.fetchone()
    return f"Desire with ID {desire_id} deleted successfully"


def __validate_desire(authentication: Authentication, desire: Desire):
    if desire.userId is None:
        raise HTTPException(detail="desire missing userId", status_code=400)
    if authentication.user_id != desire.userId:
        raise HTTPException(detail="User is not authenticated to create this resource", status_code=401)
    if desire.name is None:
        raise HTTPException(detail="desire missing a name", status_code=400)
    elif len(desire.name) == 0:
        raise HTTPException(detail="desire missing a name", status_code=400)
    elif len(desire.name) > 42:
        raise HTTPException(detail="desire name must not exceed 42 characters", status_code=400)
    if desire.dateCreated is None:
        raise HTTPException(detail="desire missing a creation date", status_code=400)
    if desire.colorR is None or desire.colorG is None or desire.colorB is None:
        raise HTTPException(detail="desire missing color", status_code=400)
    if desire.colorR < 0 or desire.colorR > 1 \
            or desire.colorB < 0 or desire.colorB > 1 \
            or desire.colorG < 0 or desire.colorG > 1:
        raise HTTPException(detail="desire does not define a valid color", status_code=400)
    if desire.priorityLevel is not None:
        if desire.priorityLevel < 0:
            raise HTTPException(detail="desire priority level must be 0 or greater", status_code=400)

#
#
# GOALS ENDPOINTS
#
#

@router.post("/api/goals")
def create_goal(authentication: Authentication, goal: Goal):
    user_id = authentication.user_id
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    __validate_goal(authentication, goal)
    stmt = goal.get_sql_insert_query()
    params = goal.get_sql_insert_params()
    cursor.execute(stmt, params)
    goal.goalId = cursor.lastrowid
    if goal.endInstant is None:
        # insert into goals_without_deadline
        cursor.execute("INSERT INTO goals_without_deadline (goal_id, user_id) VALUES (%s, %s);",
                       (goal.goalId, goal.userId))
    else:
        # insert into goals_in_day
        stmt, params = goal.get_sql_goals_in_day_insert_query_and_params()
        cursor.execute(stmt, params)

    return {"message": "Goal created successfully", "goal_id": goal.goalId}


@router.get("/api/goals/by-goal-id/{goal_id}")
def get_goal(authentication: Authentication, goal_id: int):
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


@router.get("/api/goals/by-days-range")
def get_goals_by_days_range(authentication: Authentication, start_day: float, end_day: Optional[float] = None):
    if end_day is None:
        end_day = start_day
    dt = datetime.fromtimestamp(start_day)
    days = []
    while dt.timestamp() <= end_day:
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        days.append(dt.timestamp())
        dt += timedelta(days=1)

    return get_goals_by_days_list(authentication, days)


@router.get("/api/goals/by-days-list")
def get_goals_by_days_list(authentication: Authentication, days: list[float]):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(status_code=401, detail="User is not authenticated, please log in")
    in_clause = ""
    year_months = set()
    for day in days:
        dt = datetime.fromtimestamp(day)
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        day = dt.timestamp()
        in_clause += str(day) + ","
        year_months.add((dt.year, dt.month))

    for year, month in year_months:
        # register what months we are accessing to generate recurrence events
        RecurrenceEndpoints.register_month_accessed_by_user(authentication, year, month)

    goals_by_day = {}
    cursor.execute("SELECT * FROM goals WHERE goal_id IN"
                   "(SELECT goal_id FROM goals_without_deadline WHERE user_id = %s)", (authentication.user_id,))
    goals_without_deadline = cursor.fetchall()
    for day in days:
        cursor.execute("SELECT * FROM goals WHERE goal_id IN"
                       "(SELECT goal_id FROM goals_in_day WHERE user_id = %s AND day = %s)",
                       (authentication.user_id, day))
        day_str = str(int(day))
        goals_by_day[day_str] = []
        for row in cursor.fetchall():
            goals_by_day[day_str].append(Goal.from_sql_res(row))
        for goal_without_deadline in goals_without_deadline:
            if goal_without_deadline[START_INSTANT] <= day:
                goals_by_day[day_str].append(Goal.from_sql_res(goal_without_deadline))
    return {"goals": goals_by_day}


@router.put("/api/goals/{goal_id}")
def update_goal(authentication: Authentication, goal_id: int, updated_goal: Goal):
    goal = get_goal(authentication, goal_id)["goal"]
    updated_goal.goalId = goal_id
    __validate_goal(authentication, updated_goal)
    cursor.execute(
        "UPDATE goals SET desire_id = %s, name = %s, how_much = %s, measuring_units = %s, start_instant = %s, end_instant = %s WHERE goal_id = %s",
        (updated_goal.desireId, updated_goal.name, updated_goal.howMuch, updated_goal.measuringUnits,
         updated_goal.startInstant, updated_goal.endInstant, goal_id))
    if goal.startInstant != updated_goal.startInstant or \
            (goal.endInstant is not None and goal.endInstant != updated_goal.endInstant):
        # time changed
        cursor.execute("DELETE FROM events_in_day WHERE event_id = %s", (goal_id,))
        query, params = updated_goal.get_sql_goals_in_day_insert_query_and_params()
        cursor.execute(query, params)  # add back to events_in_day
    return {"message": f"Goal with ID {goal_id} updated successfully"}


@router.delete("/api/goals/{goal_id}")
def delete_goal(authentication: Authentication, goal_id: int):
    get_goal(authentication, goal_id)
    cursor.execute("DELETE FROM goals_in_day WHERE goal_id = %s", (goal_id,))
    cursor.execute("DELETE FROM goals_without_deadline WHERE goal_id = %s", (goal_id,))
    cursor.execute("DELETE FROM goals WHERE goal_id = %s", (goal_id,))
    return {"message": f"Goal with ID {goal_id} deleted successfully"}


def __validate_goal(authentication: Authentication, goal: Goal):
    if goal.userId is None:
        raise HTTPException(detail="goal missing userId", status_code=400)
    if authentication.user_id != goal.userId:
        raise HTTPException(detail="User is not authenticated to create this resource", status_code=401)
    if goal.name is None:
        raise HTTPException(detail="goal missing a name", status_code=400)
    elif len(goal.name) == 0:
        raise HTTPException(detail="goal missing a name", status_code=400)
    elif len(goal.name) > 42:
        raise HTTPException(detail="goal name must not exceed 42 characters", status_code=400)
    if goal.howMuch is None:
        raise HTTPException(detail="goal missing how much attribute", status_code=400)
    elif goal.howMuch <= 0:
        raise HTTPException(detail="how much attribute must be greater than 0", status_code=400)
    if goal.measuringUnits is not None:
        if len(goal.measuringUnits) > 12:
            raise HTTPException(detail="measuring units cannot exceed 12 characters", status_code=400)
    if goal.startInstant is None:
        raise HTTPException(detail="goal missing start instant", status_code=400)
    if goal.endInstant is not None:
        if goal.endInstant < goal.startInstant:
            raise HTTPException(detail="goal's end instant cannot be less than its start instant", status_code=400)
    if goal.desireId is None:
        raise HTTPException(detail="goal missing a linked desire", status_code=400)
    # check authentication on desireId
    get_desire(authentication, goal.desireId)
    # check authentication on recurrenceId
    if goal.recurrenceId is not None:
        RecurrenceEndpoints.get_recurrence(authentication, goal.recurrenceId)


#
#
# PLANS ENDPOINTS
#
#

@router.post("/api/plans")
def create_plan(authentication: Authentication, plan: Plan):
    user_id = authentication.user_id
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    __validate_plan(authentication, plan)
    stmt = plan.get_sql_insert_query()
    params = plan.get_sql_insert_params()
    cursor.execute(stmt, params)
    plan_id = cursor.lastrowid
    return {"message": "Plan created successfully", "plan_id": plan_id}


@router.get("/api/plans/{plan_id}")
def get_plan(authentication: Authentication, plan_id: int):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    cursor.execute("SELECT * FROM plans WHERE plan_id = %s", (plan_id,))
    res = cursor.fetchone()
    if res is None:
        raise HTTPException(detail="no such plan exists", status_code=404)
    if authentication.user_id != res["user_id"]:
        raise HTTPException(detail="User is not authorized to access this object", status_code=401)
    return {"plan": Plan.from_sql_res(res)}


@router.get("/api/plans")
def get_plans_by_goal_id(authentication: Authentication, goal_id: int):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    cursor.execute("SELECT * FROM plans WHERE goal_id = %s", (goal_id,))
    res_list = cursor.fetchall()
    plans = []
    for res in res_list:
        plans.append(Plan.from_sql_res(res))
    return {"plans": plans}


@router.get("/api/plans")
def get_plans_by_goal_ids(authentication: Authentication, goal_ids: Annotated[list[int], Query()]):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    in_stmt = ""
    for goal_id in goal_ids:
        in_stmt += str(goal_id) + ","
    cursor.execute("SELECT * FROM plans WHERE goal_id IN %s", (in_stmt[:len(in_stmt) - 2]))
    res = cursor.fetchall()
    plansByGoalId = {}
    for row in res:
        if plansByGoalId[row["goal_id"]] is None:
            plansByGoalId[row["goal_id"]] = []
        plansByGoalId[row["goal_id"]].append(row)
    return {"plans": plansByGoalId}


@router.put("/api/plans/{plan_id}")
def update_plan(authentication: Authentication, plan_id: int, updated_plan: Plan):
    original_plan = get_plan(authentication, plan_id)["plan"]
    updated_plan.planId = plan_id
    if updated_plan.goalId is None:
        updated_plan.goalId = original_plan.goalId
    if updated_plan.eventId is None:
        updated_plan.eventId = original_plan.eventId
    __validate_plan(authentication, updated_plan)
    cursor.execute(
        "UPDATE plans SET goal_id = %s, event_id = %s, how_much = %s, howMuchAccomplished = %s, notes = %s WHERE plan_id = %s;",
        (updated_plan.goalId, updated_plan.eventId, updated_plan.howMuch, updated_plan.howMuchAccomplished,
         updated_plan.notes, plan_id))
    return {"message": f"Plan with ID {plan_id} updated successfully"}


@router.delete("/api/plans/{plan_id}")
def delete_plan(authentication: Authentication, plan_id: int):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    get_plan(authentication, plan_id)
    cursor.execute("DELETE FROM plans WHERE plan_id = %s", (plan_id,))
    return {"message": f"Plan with ID {plan_id} deleted successfully"}


def __validate_plan(authentication: Authentication, plan: Plan):
    if plan.userId is None:
        raise HTTPException(detail="plan missing userId", status_code=400)
    if authentication.user_id != plan.userId:
        raise HTTPException(detail="User is not authenticated to create this resource", status_code=401)
    if plan.howMuch is None:
        raise HTTPException(detail="plan missing how much attribute", status_code=400)
    elif plan.howMuch <= 0:
        raise HTTPException(detail="how much attribute must be greater than 0", status_code=400)
    if plan.howMuchAccomplished is not None:
        if plan.howMuchAccomplished < 0:
            raise HTTPException(detail="plan's how much accomplished attribute must be 0 or greater", status_code=400)
    if plan.goalId is None:
        raise HTTPException(detail="plan missing a linked goal", status_code=400)
    if plan.notes is not None:
        if len(plan.notes) > 300:
            raise HTTPException(detail="plans notes must not exceed 300 characters", status_code=400)
    # check authentication on goalId
    get_goal(authentication, plan.goalId)
    # check authentication on eventId
    if plan.eventId is None:
        raise HTTPException(detail="plan missing a linked event", status_code=400)
    CalendarEventEndpoints.get_calendar_event(authentication, plan.eventId)
