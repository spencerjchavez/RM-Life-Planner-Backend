from models.CalendarEvent import CalendarEvent
from models.Authentication import Authentication
from testing.test_scripts.UserEndpointsTest import UserEndpointsTest
from testing.sample_objects.Users import *
from testing.sample_objects.calendar_items.events import *
import requests
from testing.test_scripts.TestingHelperFunctions import *


class CalendarEventTests:

    def __init__(self, base_url: str, user_tests: UserEndpointsTest):
        self.event_url = base_url + "/calendar/events"
        self.base_url = base_url
        self.user_tests = user_tests

    def launch_test(self):
        print("resetting the database")
        requests.post(self.base_url + "/testing/reset_tables")
        print("databases successfully reset")

        user1_auth = self.user_tests.test_register_user(USER1)
        user2_auth = self.user_tests.test_register_user(USER2)
        user3_auth = self.user_tests.test_register_user(USER3)

        DO_HOMEWORK_EVENT.eventId = self.test_create_event(DO_HOMEWORK_EVENT, user1_auth)
        res = self.test_get_event(DO_HOMEWORK_EVENT.eventId, user1_auth)
        assert_equality(DO_HOMEWORK_EVENT, res)

    def test_create_event(self, event: CalendarEvent, authentication: Authentication,
                          expected_response_code: int = 200):
        event.userId = authentication.user_id
        res = requests.post(self.event_url, json=create_authenticated_request_body("event", event, authentication))
        compare_responses(res, expected_response_code)
        return res.json()["event_id"]

    def test_get_event(self, event_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.event_url + "/" + str(event_id),
                           json=authentication.json())
        compare_responses(res, expected_response_code)
        return res

    def test_update_event(self, event_id: int, updated_event: CalendarEvent, authentication: Authentication,
                          expected_response_code: int = 200):
        updated_event.userId = authentication.user_id
        res = requests.put(self.event_url + "/" + str(event_id),
                           json=create_authenticated_request_body("updated_event", updated_event, authentication))
        compare_responses(res, expected_response_code)

    def test_delete_event(self, event_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.delete(self.event_url + "/" + str(event_id), json=authentication.json())
        compare_responses(res, expected_response_code)
