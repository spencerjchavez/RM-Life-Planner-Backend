import requests
from testing.test_scripts.TestingHelperFunctions import *
from models.Goal import Goal
from models.Authentication import Authentication


class GoalsTests:

    def __init__(self, goals_url: str):
        self.goals_url = goals_url

    def test_create_goal(self, goal: Goal, authentication: Authentication, expected_response_code: int = 200):
        res = requests.post(self.goals_url, json=create_authenticated_request_body("goal", goal, authentication))
        compare_responses(res, expected_response_code)
        return res.json()["goal_id"]

    def test_get_goal(self, goal_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.goals_url + "/" + str(goal_id),
                           json=authentication.json())
        compare_responses(res, expected_response_code)
        return res

    def test_update_goal(self, goal_id: int, updated_goal: Goal, authentication: Authentication,
                           expected_response_code: int = 200):
        res = requests.put(self.goals_url + "/" + str(goal_id),
                           json=create_authenticated_request_body("updated_goal", updated_goal, authentication))
        compare_responses(res, expected_response_code)

    def test_delete_goal(self, goal_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.delete(self.goals_url + "/" + str(goal_id), json=authentication.json())
        compare_responses(res, expected_response_code)
