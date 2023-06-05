import json
from enum import Enum

import mysql.connector
from mysql.connector import Error
from fastapi import APIRouter, HTTPException
from goal_achieving.DesireAsParameter import DesireAsParameter
from goal_achieving.Desire import Desire
from goal_achieving.PlanAsParameter import PlanAsParameter
from goal_achieving.Plan import Plan
from goal_achieving.GoalAsParameter import GoalAsParameter
from goal_achieving.Goal import Goal
from goal_achieving.ActionAsParameter import ActionAsParameter
from goal_achieving.Action import Action
from goal_achieving.DesireCategoryAsParameter import DesireCategoryAsParameter
from goal_achieving.DesireCategory import DesireCategory
from users import UsersEndpoint

router = APIRouter()


class GoalAchievingEndpoint:

    desires_url = "/api/desires"
    goals_url = "/api/goals"
    plans_url = "/api/plans"
    actions_url = "/api/actions"

    desires_per_user_limit = 50
    desire_categories_per_user_limit = 10
    goals_per_desire_limit = 20


    class TodoTimeframe(Enum):
        DAY = 1
        WEEK = 2
        MONTH = 3

    class Success(Enum):
        UNKNOWN = 0
        SUCCESSFUL = 1
        UNSUCCESSFUL = 2
        PARTIAL = 3

    try:
        google_db_connection = mysql.connector.connect(
            host='34.31.57.31',
            database='goal_achieving',
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
    def create_desire(user_id: int, api_key: str, desire: DesireAsParameter):
        if not UsersEndpoint.authenticate(user_id, api_key):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        if user_id != desire.user_id:
            raise HTTPException(detail="bruh are you seriously trying to troll me rn? #nicetry #reported #getrekt", status_code=401)

        GoalAchievingEndpoint.cursor.execute("SELECT * FROM desire_ids_by_user WHERE user_id = %s", user_id)
        res = GoalAchievingEndpoint.cursor.fetchone()
        if res is None:
            raise HTTPException(detail="uh-oh, we didn't correctly initialize your data! Hmu @ sjchavez99@gmail.com and I'll fix the issue", status_code=500)
        desire_ids_bytes = res["desire_ids"]
        if len(desire_ids_bytes) > GoalAchievingEndpoint.desires_per_user_limit * 4:
            raise HTTPException(detail="User cannot create any more desires", status_code=400)

        query = """
            INSERT INTO desires (name, user_id, deadline_date, category_id, priority_level, related_goal_ids)
            VALUES (:name, :user_id, :deadline_date, :category_id, :priority_level, :related_goal_ids)
        """
        params = {
            "name": desire.name,
            "user_id": user_id,
            "deadline_date": desire.deadlineDate,
            "category_id": desire.categoryId,
            "priority_level": desire.priorityLevel,
        }
        GoalAchievingEndpoint.cursor.execute(query, params)
        desire_ids_bytes += GoalAchievingEndpoint.cursor.lastrowid.to_bytes(4, "big", signed=False)
        GoalAchievingEndpoint.cursor.execute("UPDATE desire_ids_by_user SET desire_ids = %s WHERE user_id = %s", (desire_ids_bytes, user_id))
        return {"message": "Desire created successfully", "desire_id": GoalAchievingEndpoint.cursor.lastrowid}, 200

    @staticmethod
    @router.get("/api/desires/{desire_id}")
    def get_desire(user_id: int, api_key: str, desire_id: int):
        if not UsersEndpoint.authenticate(user_id, api_key):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        GoalAchievingEndpoint.cursor.execute("SELECT * FROM desires WHERE desire_id = %s", desire_id.__str__())
        desire_dict = GoalAchievingEndpoint.cursor.fetchone().__dict__
        if desire_dict["user_id"] != user_id:
            raise HTTPException(detail="User is not authenticated to access this objcet", status_code=401)
        return {"message": "successfully got desire", "desire": json.dumps(desire_dict)}, 200

    @staticmethod
    @router.put("/api/desires/{desire_id}")
    def update_desire(user_id: int, api_key: str, desire_id: int, updated_desire: DesireAsParameter):
        if not UsersEndpoint.authenticate(user_id, api_key):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        res = GoalAchievingEndpoint.get_desire(desire_id)
        if res[1] != 200:
            raise HTTPException(status_code=404, detail="Desire not found")
        GoalAchievingEndpoint.cursor.execute("SELECT * FROM desires WHERE desire_id = %s", desire_id)
        if GoalAchievingEndpoint.cursor.fetchone()["user_id"] != user_id:
            raise HTTPException(detail="User is not authenticated to access this object", status_code=401)

        query = "UPDATE desires SET name = %s, deadline_date = %s, category_id = %s, priority_level = %s, related_goal_ids = %s WHERE desire_id = %s"
        params = (updated_desire.name, updated_desire.deadlineDate, updated_desire.categoryId, updated_desire.priorityLevel, updated_desire.relatedGoalIds, desire_id)
        GoalAchievingEndpoint.cursor.execute(query, params)
        return f"Desire with ID {desire_id} updated successfully", 200

    @staticmethod
    @router.delete("/api/desires/{desire_id}")
    def delete_desire(user_id: int, api_key: str, desire_id: int):
        if not UsersEndpoint.authenticate(user_id, api_key):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        GoalAchievingEndpoint.cursor.execute("SELECT * FROM desires WHERE desire_id = %s", desire_id)
        if GoalAchievingEndpoint.cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Desire not found")
        if GoalAchievingEndpoint.cursor.fetchone()["user_id"] != user_id.__str__():
            raise HTTPException(detail="User is not authorized to access this element", status_code=401)
        GoalAchievingEndpoint.cursor.execute("DELETE FROM desires WHERE desire_id = %s", desire_id)

        GoalAchievingEndpoint.cursor.execute("SELECT * FROM desire_ids_by_user WHERE user_id = %s", user_id)
        desire_ids_bytes: bytes = GoalAchievingEndpoint.cursor.fetchone()["desire_ids"]
        desire_id_bytes = desire_id.to_bytes(4, "big", signed=False)
        index = 0
        while True:
            index = desire_ids_bytes.find(desire_id_bytes, index)
            if index == -1:
                print("ERROR: desire was created in desires database but not found in desires_ids_by_user database")
                return f"Desire with ID {desire_id} deleted successfully", 200
            if index % 4 == 0:
                desire_ids_bytes = desire_ids_bytes[:index] + desire_ids_bytes[index+4:]
                break
            index += 1
        GoalAchievingEndpoint.cursor.execute("UPDATE desire_ids_by_user SET desire_ids = %s", desire_ids_bytes)
        return f"Desire with ID {desire_id} deleted successfully", 200

    # DESIRE CATEGORIES ENDPOINT
    @staticmethod
    @router.post("/api/desires/categories")
    def create_desire_category(user_id: int, api_key: str, desire: DesireCategoryAsParameter):
        if not UsersEndpoint.authenticate(user_id, api_key):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        GoalAchievingEndpoint.cursor.execute("INSERT INTO desire_categories (name, user_id, color_r, color_g, color_b) VALUES (%s, %s, %s, %s, %s)",
                                             desire.name, desire.userId, desire.colorR, desire.colorG, desire.colorB)
        category_id = GoalAchievingEndpoint.cursor.lastrowid
        GoalAchievingEndpoint.cursor.execute("SELECT * FROM desire_category_ids_by_user WHERE user_id = %s", user_id)
        category_ids_bytes = GoalAchievingEndpoint.cursor.fetchone()["category_ids"]
        # TODO add category_id to bytes
        # TODO create a bytes helper class to make this stuff easier
        return {"message": "Desire created successfully", "category_id": GoalAchievingEndpoint.cursor.lastrowid}, 200

    @staticmethod
    @router.get("/api/desires/categories/{category_id}")
    def get_desire_category(user_id: int, api_key: str, desire_id: int):
        if not UsersEndpoint.authenticate(user_id, api_key):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        GoalAchievingEndpoint.cursor.execute("SELECT * FROM desire_categories WHERE desire_id = %s", desire_id)
        if GoalAchievingEndpoint.cursor.rowcount == 0:
            raise HTTPException(detail="no such desire_id exists: " + desire_id.__str__(), status_code=400)
        res = GoalAchievingEndpoint.cursor.fetchone().__dict__
        if res["user_id"] != user_id:
            raise HTTPException(detail="User is not authenticated to access this element", status_code=401)
        return res.__dict__, 200

    @staticmethod
    @router.put("/api/desires/categories{category_id}")
    def update_desire(user_id: int, api_key: str, category_id: int, updated_category: DesireCategoryAsParameter):
        if not UsersEndpoint.authenticate(user_id, api_key):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        GoalAchievingEndpoint.cursor.execute("SELECT * FROM desire_categories WHERE category_id = %s", category_id)
        res = GoalAchievingEndpoint.cursor.fetchone()
        if res is None:
            raise HTTPException(status_code=400, detail="Desire category not found")
        if res["user_id"] != user_id.__str__():
            raise HTTPException(detail="User is not authenticated to access this element", status_code=401)
        GoalAchievingEndpoint.cursor.execute("UPDATE desire_categories SET name = %s user_id = %s color_r = %s color_g = %s color_b = %s WHERE category_id = %s", (updated_category.name, updated_category.userId, updated_category.colorR, updated_category.colorG, updated_category.colorB, category_id))
        return {"message": f"Desire category with ID {category_id} updated successfully"}, 200

    @staticmethod
    @router.delete("/api/desires/categories/{category_id}")
    def delete_desire_category(user_id: int, api_key: str, category_id: int):
        if not UsersEndpoint.authenticate(user_id, api_key):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        GoalAchievingEndpoint.cursor.execute("SELECT * FROM desire_categories WHERE category_id = %s", category_id)
        res = GoalAchievingEndpoint.cursor.fetchone()
        if res is None:
            raise HTTPException(status_code=400, detail="Desire category not found")
        if res["user_id"] != user_id.__str__():
            raise HTTPException(detail="User is not authenticated to access this element", status_code=401)
        GoalAchievingEndpoint.cursor.execute("DELETE FROM desire_categories WHERE category_id = %s", category_id)
        return {"message": f"Desire category with ID {category_id} deleted successfully"}, 200

    # GOALS ENDPOINTS
    @staticmethod
    @router.post("/api/goals")
    def create_goal(user_id: int, api_key: str, goal: GoalAsParameter):
        if not UsersEndpoint.authenticate(user_id, api_key):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        if user_id != goal.userId:
            print("ALERT ALERT ALERT: GoalAchievingEndpoint create-goal user ids didn't match: %s and %s", (user_id, goal.userId))
            raise HTTPException(detail="bruh are you seriously trying to troll me rn? #nicetry #reported #getrekt", status_code=401)
        GoalAchievingEndpoint.cursor.execute("SELECT * FROM goal_ids_by_desire WHERE desire_id = %s", goal.desireId)
        res = GoalAchievingEndpoint.cursor.fetchone()
        if res is None:
            raise HTTPException(detail="no such desire_id exists", status_code=400)
        if res["user_id"] != user_id:
            print("ALERT ALERT ALERT: GoalAchievingEndpoint create-goal user ids didn't match: %s and %s", (user_id, res["user_id"]))
            raise HTTPException(detail="bruh are you seriously trying to troll me rn? #nicetry #reported #getrekt", status_code=401)
        goal_ids_bytes = res["goal_ids"]
        if len(goal_ids_bytes) >= GoalAchievingEndpoint.goals_per_desire_limit * 4:
            raise HTTPException(detail="Max number of goals created for specified desire", status_code=400)

        GoalAchievingEndpoint.cursor.execute("INSERT INTO goals COLUMNS user_id, name, how_much, measuring_units, rrule_string  VALUES (%s, %s, %s, %s, %s);",
                                             (goal.userId, goal.name, goal.howMuch, goal.measuringUnits, goal.rruleString))
        goal_id = GoalAchievingEndpoint.cursor.lastrowid
        goal_ids_bytes += goal_id.to_bytes(length=4, byteorder="big", signed=False)
        GoalAchievingEndpoint.cursor.execute("UPDATE goal_ids_by_desire SET goal_ids = %s WHERE desire_id = %s", (goal_ids_bytes, goal.desireId))
        return {"message": "Goal created successfully", "goal_id": goal_id}, 200

    @staticmethod
    @router.get("/api/goals/{goal_id}")
    def get_goals(user_id: int, api_key: str, goal_id: int):
        if not UsersEndpoint.authenticate(user_id, api_key):
            raise HTTPException(detail="User is not authenticated, please log in", status_code=401)
        GoalAchievingEndpoint.cursor.execute("SELECT * FROM ")
    @staticmethod
    @router.put("/api/goals/{goal_id}")
    def update_goal(goal_id: int, updated_goal: dict):
        if goal_id < len(goals):
            goals[goal_id] = updated_goal
            return {"message": f"Goal with ID {goal_id} updated successfully"}
        raise HTTPException(status_code=404, detail="Goal not found")

    @staticmethod
    @router.delete("/api/goals/{goal_id}")
    def delete_goal(goal_id: int):
        if goal_id < len(goals):
            del goals[goal_id]
            return {"message": f"Goal with ID {goal_id} deleted successfully"}
        raise HTTPException(status_code=404, detail="Goal not found")

    # PLANS ENDPOINTS
    @staticmethod
    @router.post("/api/plans")
    def create_plan(plan: dict):
        plans.append(plan)
        return {"message": "Plan created successfully"}

    @staticmethod
    @router.get("/api/plans")
    def get_plans():
        return plans

    @staticmethod
    @router.put("/api/plans/{plan_id}")
    def update_plan(plan_id: int, updated_plan: dict):
        if plan_id < len(plans):
            plans[plan_id] = updated_plan
            return {"message": f"Plan with ID {plan_id} updated successfully"}
        raise HTTPException(status_code=404, detail="Plan not found")

    @staticmethod
    @router.delete("/api/plans/{plan_id}")
    def delete_plan(plan_id: int):
        if plan_id < len(plans):
            del plans[plan_id]
            return {"message": f"Plan with ID {plan_id} deleted successfully"}
        raise HTTPException(status_code=404, detail="Plan not found")

    # ACTIONS ENDPOINT
    @staticmethod
    @router.post("/api/actions")
    def create_action(action: dict):
        actions.append(action)
        return {"message": "Action created successfully"}

    @staticmethod
    @router.get("/api/actions")
    def get_actions():
        return actions

    @staticmethod
    @router.put("/api/actions/{action_id}")
    def update_action(action_id: int, updated_action: dict):
        if action_id < len(actions):
            actions[action_id] = updated_action
            return {"message": f"Action with ID {action_id} updated successfully"}
        raise HTTPException(status_code=404, detail="Action not found")

    @staticmethod
    @router.delete("/api/actions/{action_id}")
    def delete_action(action_id: int):

