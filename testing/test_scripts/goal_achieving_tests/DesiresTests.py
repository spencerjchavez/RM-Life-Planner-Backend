import requests
from testing.test_scripts.TestingHelperFunctions import *
from models.Desire import Desire
from models.Authentication import Authentication


class DesiresTests:

    def __init__(self, desire_url: str):
        self.desire_url = desire_url

    def test_create_desire(self, desire: Desire, authentication: Authentication, expected_response_code: int = 200):
        res = requests.post(self.desire_url, json=create_authenticated_request_body("desire", desire, authentication))
        compare_responses(res, expected_response_code)
        return res.json()["desire_id"]

    def test_get_desire(self, desire_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.desire_url + "/" + str(desire_id),
                           json=authentication.json())
        compare_responses(res, expected_response_code)
        return res

    def test_update_desire(self, desire_id: int, updated_desire: Desire, authentication: Authentication,
                           expected_response_code: int = 200):
        res = requests.put(self.desire_url + "/" + str(desire_id),
                           json=create_authenticated_request_body("updated_desire", updated_desire, authentication))
        compare_responses(res, expected_response_code)

    def test_delete_desire(self, desire_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.delete(self.desire_url + "/" + str(desire_id), json=authentication.json())
        compare_responses(res, expected_response_code)
