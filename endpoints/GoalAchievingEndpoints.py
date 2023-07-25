# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from mysql.connector.cursor import MySQLCursor
from fastapi import APIRouter, HTTPException
from models.Desire import Desire
from models.Plan import Plan
from models.Goal import Goal
from models.Action import Action
from endpoints import UserEndpoints
from models.Authentication import Authentication
from models.SQLColumnNames import *
import time
from mysql.connector.cursor import MySQLCursor, Error



desires_url = "/api/desires"
goals_url = "/api/goals"
plans_url = "/api/plans"
actions_url = "/api/actions"

desires_per_user_limit = 50
desire_categories_per_user_limit = 10
goals_per_desire_limit = 20

router = APIRouter()
cursor: MySQLCursor


# DESIRE ENDPOINTS
@router.post("/api/desires")
def create_desire(authentication: Authentication, desire: Desire):
    user_id = authentication.user_id
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    if user_id != desire.userId:
        raise HTTPException(detail="bruh are you seriously trying to troll me rn? #nicetry #reported #getrekt", status_code=401)

    desire.dateCreated = time.time()
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
        return "no such desire_id found!", 404
    if res["user_id"] != user_id:
        raise HTTPException(detail="User is not authenticated to access this resource", status_code=401)
    return {"message": "successfully got desire", "desire": res.__dict__}


@router.put("/api/desires/{desire_id}")
def update_desire(authentication: Authentication, desire_id: int, updated_desire: Desire):
    get_desire(desire_id)
    query = f"UPDATE desires SET {NAME} = %s, {DEADLINE} = %s, {DATE_RETIRED} = %s, {PRIORITY_LEVEL} = %s,  {COLOR_R} = %s, {COLOR_G} = %s, {COLOR_B} = %s WHERE desire_id = %s"
    params = (updated_desire.name, updated_desire.deadline, updated_desire.dateRetired, updated_desire.priorityLevel, updated_desire.colorR, updated_desire.colorG, updated_desire.colorB, desire_id)
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
    return f"Desire with ID {desire_id} deleted successfully"


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
    if user_id != goal.userId:
        print("ALERT ALERT ALERT: GoalAchievingEndpoint create-goal user ids didn't match: %s and %s", (user_id, goal.userId))
        raise HTTPException(detail="bruh are you seriously trying to troll me rn? #nicetry #reported #getrekt", status_code=401)

    stmt = goal.get_sql_insert_query()
    params = goal.get_sql_insert_params()
    cursor.execute(stmt, params)
    goal_id = cursor.lastrowid
    return {"message": "Goal created successfully", "goal_id": goal_id}


@router.get("/api/goals/{goal_id}")
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
    return {"goal: ": res}


@router.put("/api/goals/{goal_id}")
def update_goal(authentication: Authentication, goal_id: int, updated_goal: Goal):
    goal_dict = get_goal(authentication, goal_id)
    cursor.execute("UPDATE goals SET desire_id = %s, name = %s, how_much = %s, measuring_units = %s, end_instant = %s WHERE goal_id = %s",
                                         (updated_goal.desireId, updated_goal.name, updated_goal.howMuch, updated_goal.measuringUnits, updated_goal.endInstant, goal_id))
    return {"message": f"Goal with ID {goal_id} updated successfully"}


@router.delete("/api/goals/{goal_id}")
def delete_goal(authentication: Authentication, goal_id: int):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    cursor.execute("SELECT * FROM goals WHERE goal_id = %s", (goal_id,))
    res = cursor.fetchone()
    if res is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    if res["user_id"] != authentication.user_id:
        raise HTTPException(detail="User not authorized to access this resource", status_code=401)

    cursor.execute("DELETE FROM goals WHERE goal_id = %s", (goal_id,))
    return {"message": f"Goal with ID {goal_id} deleted successfully"}


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
    if user_id != plan.userId:
        raise HTTPException(detail="User not authorized to create this object", status_code=401)
    stmt = plan.get_sql_insert_query()
    params = plan.get_sql_insert_params()
    cursor.execute(stmt, params)
    plan_id = cursor.lastrowid
    return {"message": "Plan created successfully", "plan_id": plan_id}


@router.get("/api/plans/{plan_id}")
def get_plan(authentication: Authentication, plan_id: int):
    user_id = authentication.user_id
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    cursor.execute("SELECT * FROM plans WHERE plan_id = %s", (plan_id,))
    res = cursor.fetchone()
    if res is None:
        raise HTTPException(detail="no such plan exists", status_code=404)
    if user_id != res["user_id"]:
        raise HTTPException(detail="User is not authorized to access this object", status_code=401)
    return {"plan": res}


@router.put("/api/plans/{plan_id}")
def update_plan(authentication: Authentication, plan_id: int, updated_plan: Plan):
    old_plan_dict = get_plan(authentication, plan_id)
    cursor.execute("UPDATE plans SET goal_id = %s, event_id = %s, how_much = %s WHERE plan_id = %s;",
                                         (updated_plan.goalId, updated_plan.eventId, updated_plan.howMuch, plan_id))
    return {"message": f"Plan with ID {plan_id} updated successfully"}


@router.delete("/api/plans/{plan_id}")
def delete_plan(authentication: Authentication, plan_id: int):
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    get_plan(authentication, plan_id)
    cursor.execute("DELETE FROM plans WHERE plan_id = %s", (plan_id,))
    return {"message": f"Plan with ID {plan_id} deleted successfully"}

#
#
# ACTIONS ENDPOINT
#
#


@router.post("/api/actions")
def create_action(authentication: Authentication, action: Action):
    get_plan(authentication, action.planId)  # authenticate
    stmt = action.get_sql_insert_query()
    params = action.get_sql_insert_params()
    cursor.execute(stmt, params)
    action_id = cursor.lastrowid
    return {"message": "Action created successfully", "action_id": action_id}


@router.get("/api/actions/{action_id}")
def get_action(authentication: Authentication, action_id: int):
    user_id = authentication.user_id
    if not UserEndpoints.authenticate(authentication):
        raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
    cursor.execute("SELECT * FROM actions WHERE action_id = %s", (action_id,))
    res = cursor.fetchone()
    if res is None:
        raise HTTPException(detail="Specified resource does not exist", status_code=404)
    if user_id != res["user_id"]:
        raise HTTPException(detail="User is not authorized to access this object", status_code=401)
    return res


@router.put("/api/actions/{action_id}")
def update_action(authentication: Authentication, action_id: int, updated_action: Action):
    get_action(authentication, action_id)  # authenticate
    cursor.execute("UPDATE actions SET successful = %s, how_much_accomplished = %s, notes = %s WHERE action_id = %s",
                                         (updated_action.successful, updated_action.howMuchAccomplished, updated_action.notes, action_id))
    return {"message": f"Action with ID {action_id} updated successfully"}


@router.delete("/api/actions/{action_id}")
def delete_action(authentication: Authentication, action_id: int):
    get_action(authentication, action_id)  # authenticate
    cursor.execute("DELETE FROM actions WHERE action_id = %s", (action_id,))
    return "success"
