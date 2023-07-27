from models.Recurrence import Recurrence
from models.Authentication import Authentication
import requests
from testing.test_scripts.TestingHelperFunctions import *


class RecurrenceTests:

    def __init__(self, recurrence_url: str):
        self.recurrence_url = recurrence_url

    def test_create_recurrence(self, recurrence: Recurrence, authentication: Authentication,
                                expected_response_code: int = 200):
        recurrence.userId = authentication.user_id
        res = requests.post(self.recurrence_url,
                            json=create_authenticated_request_body("recurrence", recurrence, authentication))
        compare_responses(res, expected_response_code)
        return res.json()["recurrence_id"]

    def test_get_recurrence(self, recurrence_id: int, authentication: Authentication,
                            expected_response_code: int = 200):
        res = requests.get(self.recurrence_url + "/" + str(recurrence_id),
                           json=authentication.json())
        compare_responses(res, expected_response_code)
        return res

    def test_update_recurrence(self, recurrence_id: int, updated_recurrence: Recurrence, authentication: Authentication,
                               expected_response_code: int = 200):
        updated_recurrence.userId = authentication.user_id
        res = requests.put(self.recurrence_url + "/" + str(recurrence_id),
                           json=create_authenticated_request_body("updated_recurrence", updated_recurrence,
                                                                  authentication))
        compare_responses(res, expected_response_code)

    def test_delete_recurrence(self, recurrence_id: int, authentication: Authentication,
                               expected_response_code: int = 200):
        res = requests.delete(self.recurrence_url + "/" + str(recurrence_id), json=authentication.json())
        compare_responses(res, expected_response_code)
