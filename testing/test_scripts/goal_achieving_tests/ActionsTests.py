import requests
from testing.test_scripts.TestingHelperFunctions import *
from models.Action import Action
from models.Authentication import Authentication


class ActionsTests:

    def __init__(self, actions_url: str):
        self.actions_url = actions_url

    def test_create_action(self, action: Action, authentication: Authentication, expected_response_code: int = 200):
        res = requests.post(self.actions_url, json=create_authenticated_request_body("action", action, authentication))
        compare_responses(res, expected_response_code)
        return res.json()["action_id"]

    def test_get_action(self, plan_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.actions_url + "/" + str(plan_id),
                           json=authentication.json())
        compare_responses(res, expected_response_code)
        return res
        
    def test_update_action(self, plan_id: int, updated_action: Action, authentication: Authentication, expected_response_code: int = 200):
        res = requests.put(self.actions_url + "/" + str(plan_id),
                           json=create_authenticated_request_body("updated_action", updated_action, authentication))
        compare_responses(res, expected_response_code)
    
    def test_delete_action(self, plan_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.delete(self.actions_url + "/" + str(plan_id), json=authentication.json())
        compare_responses(res, expected_response_code)
        