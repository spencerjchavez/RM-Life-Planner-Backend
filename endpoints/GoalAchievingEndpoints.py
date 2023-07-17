# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from enum import Enum
import mysql.connector
from mysql.connector import Error
from fastapi import APIRouter, HTTPException
from models.Desire import Desire
from models.Plan import Plan
from models.Goal import Goal
from models.Action import Action
from endpoints import UserEndpoints
from models.Authentication import Authentication
from models.SQLColumnNames import SQLColumnNames as _

router = APIRouter()


class GoalAchievingEndpoint:

    class Success(Enum):
        UNKNOWN = 0
        SUCCESSFUL = 1
        UNSUCCESSFUL = 2
        PARTIAL = 3

    desires_url = "/api/desires"
    goals_url = "/api/goals"
    plans_url = "/api/plans"
    actions_url = "/api/actions"

    desires_per_user_limit = 50
    desire_categories_per_user_limit = 10
    goals_per_desire_limit = 20

    try:
        google_db_connection = mysql.connector.connect(
            host='34.31.57.31',
            database='database1',
            user='root',
            password='supersecretdatabase$$keepout',
            autocommit=True
        )
        connection = google_db_connection
        cursor = connection.cursor(dictionary=True)
        if connection.is_connected():
            print('Connected to goal_achieving database')
    except Error as e:
        print(f'Error connecting to MySQL database: {e}')

    # DESIRE ENDPOINTS
    @staticmethod
    @router.post("/api/desires")
    def create_desire(authentication: Authentication, desire: Desire):
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        if user_id != desire.userId:
            raise HTTPException(detail="bruh are you seriously trying to troll me rn? #nicetry #reported #getrekt", status_code=401)

        query = desire.get_sql_insert_query()
        params = desire.get_sql_insert_params()
        GoalAchievingEndpoint.cursor.execute(query, params)
        return {"message": "Desire created successfully", "desire_id": GoalAchievingEndpoint.cursor.lastrowid}, 200

    @staticmethod
    @router.get("/api/desires/{desire_id}")
    def get_desire(authentication: Authentication, desire_id: int):
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        GoalAchievingEndpoint.cursor.execute("SELECT * FROM desires WHERE desire_id = %s", (desire_id,))
        res = GoalAchievingEndpoint.cursor.fetchone()
        if res is None:
            return "no such desire_id found!", 404
        if res["user_id"] != user_id:
            raise HTTPException(detail="User is not authenticated to access this resource", status_code=401)
        return {"message": "successfully got desire", "desire": res.__dict__}, 200

    @staticmethod
    @router.put("/api/desires/{desire_id}")
    def update_desire(authentication: Authentication, desire_id: int, updated_desire: Desire):
        GoalAchievingEndpoint.get_desire(desire_id)
        query = f"UPDATE desires SET {_.NAME} = %s, {_.DEADLINE} = %s, {_.DATE_RETIRED} = %s, {_.PRIORITY_LEVEL} = %s,  {_.COLOR_R} = %s, {_.COLOR_G} = %s, {_.COLOR_B} = %s WHERE desire_id = %s"
        params = (updated_desire.name, updated_desire.deadline, updated_desire.dateRetired, updated_desire.priorityLevel, updated_desire.colorR, updated_desire.colorG, updated_desire.colorB, desire_id)
        GoalAchievingEndpoint.cursor.execute(query, params)
        return f"Desire with ID {desire_id} updated successfully", 200

    @staticmethod
    @router.delete("/api/desires/{desire_id}")
    def delete_desire(authentication: Authentication, desire_id: int):
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        GoalAchievingEndpoint.cursor.execute("SELECT * FROM desires WHERE desire_id = %s", (desire_id,))
        res = GoalAchievingEndpoint.cursor.fetchone()
        if res is None:
            raise HTTPException(status_code=404, detail="Desire not found")
        if res["user_id"] != user_id:
            raise HTTPException(detail="User is not authorized to access this resource", status_code=401)

        GoalAchievingEndpoint.cursor.execute("DELETE FROM desires WHERE desire_id = %s", (desire_id,))
        return f"Desire with ID {desire_id} deleted successfully", 200

    #
    #
    # GOALS ENDPOINTS
    #
    #
    @staticmethod
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
        GoalAchievingEndpoint.cursor.execute(stmt, params)
        goal_id = GoalAchievingEndpoint.cursor.lastrowid
        return {"message": "Goal created successfully", "goal_id": goal_id}, 200

    @staticmethod
    @router.get("/api/goals/{goal_id}")
    def get_goal(authentication: Authentication, goal_id: int):
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        GoalAchievingEndpoint.cursor.execute("SELECT * FROM goals WHERE goal_id = %s", (goal_id,))
        res = GoalAchievingEndpoint.cursor.fetchone()
        if res is None:
            raise HTTPException(detail="No goal of specified id found", status_code=404)
        if res["user_id"] != user_id:
            raise HTTPException(detail="User is not authorized to access this resource", status_code=401)
        return {"goal: ": res}, 200

    @staticmethod
    @router.put("/api/goals/{goal_id}")
    def update_goal(authentication: Authentication, goal_id: int, updated_goal: Goal):
        goal_dict = GoalAchievingEndpoint.get_goal(authentication, goal_id)[0]
        GoalAchievingEndpoint.cursor.execute("UPDATE goals SET desire_id = %s, name = %s, how_much = %s, measuring_units = %s, end_instant = %s WHERE goal_id = %s",
                                             (updated_goal.desireId, updated_goal.name, updated_goal.howMuch, updated_goal.measuringUnits, updated_goal.endInstant, goal_id))
        return {"message": f"Goal with ID {goal_id} updated successfully"}, 200

    @staticmethod
    @router.delete("/api/goals/{goal_id}")
    def delete_goal(authentication: Authentication, goal_id: int):
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        GoalAchievingEndpoint.cursor.execute("SELECT * FROM goals WHERE goal_id = %s", (goal_id,))
        res = GoalAchievingEndpoint.cursor.fetchone()
        if res is None:
            raise HTTPException(status_code=404, detail="Goal not found")
        if res["user_id"] != authentication.user_id:
            raise HTTPException(detail="User not authorized to access this resource", status_code=401)

        GoalAchievingEndpoint.cursor.execute("DELETE FROM goals WHERE goal_id = %s", (goal_id,))
        return {"message": f"Goal with ID {goal_id} deleted successfully"}

    #
    #
    # PLANS ENDPOINTS
    #
    #

    @staticmethod
    @router.post("/api/plans")
    def create_plan(authentication: Authentication, plan: Plan):
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        if user_id != plan.userId:
            raise HTTPException(detail="User not authorized to create this object", status_code=401)
        stmt = plan.get_sql_insert_query()
        params = plan.get_sql_insert_params()
        GoalAchievingEndpoint.cursor.execute(stmt, params)
        plan_id = GoalAchievingEndpoint.cursor.lastrowid
        return {"message": "Plan created successfully", "plan_id": plan_id}, 200

    @staticmethod
    @router.get("/api/plans/{plan_id}")
    def get_plan(authentication: Authentication, plan_id: int):
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        GoalAchievingEndpoint.cursor.execute("SELECT * FROM plans WHERE plan_id = %s", (plan_id,))
        res = GoalAchievingEndpoint.cursor.fetchone()
        if res is None:
            raise HTTPException(detail="no such plan exists", status_code=404)
        if user_id != res["user_id"]:
            raise HTTPException(detail="User is not authorized to access this object", status_code=401)
        return {"plan": res}, 200

    @staticmethod
    @router.put("/api/plans/{plan_id}")
    def update_plan(authentication: Authentication, plan_id: int, updated_plan: Plan):
        old_plan_dict = GoalAchievingEndpoint.get_plan(authentication, plan_id)[0]
        GoalAchievingEndpoint.cursor.execute("UPDATE plans SET goal_id = %s, event_id = %s, how_much = %s WHERE plan_id = %s;",
                                             (updated_plan.goalId, updated_plan.eventId, updated_plan.howMuch, plan_id))
        return {"message": f"Plan with ID {plan_id} updated successfully"}, 200

    @staticmethod
    @router.delete("/api/plans/{plan_id}")
    def delete_plan(authentication: Authentication, plan_id: int):
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        GoalAchievingEndpoint.get_plan(authentication, plan_id)
        GoalAchievingEndpoint.cursor.execute("DELETE FROM plans WHERE plan_id = %s", (plan_id,))
        return {"message": f"Plan with ID {plan_id} deleted successfully"}

    #
    #
    # ACTIONS ENDPOINT
    #
    #

    @staticmethod
    @router.post("/api/actions")
    def create_action(authentication: Authentication, action: Action):
        GoalAchievingEndpoint.get_plan(authentication, action.planId)  # authenticate
        stmt = action.get_sql_insert_query()
        params = action.get_sql_insert_params()
        GoalAchievingEndpoint.cursor.execute(stmt, params)
        action_id = GoalAchievingEndpoint.cursor.lastrowid
        return {"message": "Action created successfully", "action_id": action_id}, 200

    @staticmethod
    @router.get("/api/actions/{action_id}")
    def get_action(authentication: Authentication, action_id: int):
        user_id = authentication.user_id
        if not UserEndpoints.authenticate(authentication):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        GoalAchievingEndpoint.cursor.execute("SELECT * FROM actions WHERE action_id = %s", (action_id,))
        res = GoalAchievingEndpoint.cursor.fetchone()
        if res is None:
            raise HTTPException(detail="Specified resource does not exist", status_code=404)
        if user_id != res["user_id"]:
            raise HTTPException(detail="User is not authorized to access this object", status_code=401)
        return res, 200

    @staticmethod
    @router.put("/api/actions/{action_id}")
    def update_action(authentication: Authentication, action_id: int, updated_action: Action):
        GoalAchievingEndpoint.get_action(authentication, action_id)  # authenticate
        GoalAchievingEndpoint.cursor.execute("UPDATE actions SET successful = %s, how_much_accomplished = %s, notes = %s WHERE action_id = %s",
                                             (updated_action.successful, updated_action.howMuchAccomplished, updated_action.notes, action_id))
        return {"message": f"Action with ID {action_id} updated successfully"}

    @staticmethod
    @router.delete("/api/actions/{action_id}")
    def delete_action(authentication: Authentication, action_id: int):
        GoalAchievingEndpoint.get_action(authentication, action_id)  # authenticate
        GoalAchievingEndpoint.cursor.execute("DELETE FROM actions WHERE action_id = %s", (action_id,))
        return "success", 200
