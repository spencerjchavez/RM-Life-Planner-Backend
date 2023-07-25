import requests
from testing.test_scripts.TestingHelperFunctions import *
from models.Plan import Plan
from models.Authentication import Authentication


class PlansTests:

    def __init__(self, plans_url: str):
        self.plans_url = plans_url

    def test_create_plan(self, plan: Plan, authentication: Authentication, expected_response_code: int = 200):
        res = requests.post(self.plans_url, json=create_authenticated_request_body("plan", plan, authentication))
        compare_responses(res, expected_response_code)
        return res.json()["plan_id"]

    def test_get_plan(self, plan_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.plans_url + "/" + str(plan_id),
                           json=authentication.json())
        compare_responses(res, expected_response_code)
        return res

    def test_update_plan(self, plan_id: int, updated_plan: Plan, authentication: Authentication,
                           expected_response_code: int = 200):
        res = requests.put(self.plans_url + "/" + str(plan_id),
                           json=create_authenticated_request_body("updated_plan", updated_plan, authentication))
        compare_responses(res, expected_response_code)

    def test_delete_plan(self, plan_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.delete(self.plans_url + "/" + str(plan_id), json=authentication.json())
        compare_responses(res, expected_response_code)
