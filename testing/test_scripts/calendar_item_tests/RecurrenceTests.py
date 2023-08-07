from models.Recurrence import Recurrence
from models.Authentication import Authentication
import requests
from testing.test_scripts.TestingHelperFunctions import *
from testing.test_scripts.UserEndpointsTest import UserEndpointsTest
from testing.test_scripts.calendar_item_tests.CalendarEventTests import CalendarEventTests
from testing.test_scripts.calendar_item_tests.ToDoTests import ToDoTests
from testing.test_scripts.goal_achieving_tests.GoalsTests import GoalsTests

from testing.sample_objects.Users import *
from testing.sample_objects.calendar_items.recurrences import *

class RecurrenceTests:

    def __init__(self, recurrence_url: str, user_tests: UserEndpointsTest, event_tests: CalendarEventTests, todo_tests: ToDoTests, goal_tests: GoalsTests):
        self.recurrence_url = recurrence_url
        self.user_tests = user_tests
        self.event_tests = event_tests
        self.todo_tests = todo_tests
        self.goal_tests = goal_tests

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
        return res.json()["recurrence"]

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

    def launch_test(self):
        user1_auth = self.user_tests.test_register_user(USER1)
        user2_auth = self.user_tests.test_register_user(USER2)
        user3_auth = self.user_tests.test_register_user(USER3)

        WEEKLY_MEETING_RECURRENCE.recurrenceId = self.test_create_recurrence(WEEKLY_MEETING_RECURRENCE, user1_auth)
        CHURCH_RECURRENCE.recurrenceId = self.test_create_recurrence(CHURCH_RECURRENCE, user1_auth)
        SERVE_SOMEONE_SUN_FRI_RECURRENCE.recurrenceId = self.test_create_recurrence(SERVE_SOMEONE_SUN_FRI_RECURRENCE, user1_auth)
        DAILY_BREAKFAST_RECURRENCE.recurrenceId = self.test_create_recurrence(DAILY_BREAKFAST_RECURRENCE, user1_auth)
        DO_SOMETHING_USEFUL_MONTHLY_RECURRENCE.recurrenceId = self.test_create_recurrence(DO_SOMETHING_USEFUL_MONTHLY_RECURRENCE, user1_auth)
        MY_BIRTHDAY_RECURRENCE.recurrenceId = self.test_create_recurrence(MY_BIRTHDAY_RECURRENCE, user1_auth)
        EAT_VEGETABLES_DAILY_RECURRENCE.recurrenceId = self.test_create_recurrence(EAT_VEGETABLES_DAILY_RECURRENCE, user1_auth)
        GO_TO_THE_TEMPLE_MONTHLY_RECURRENCE.recurrenceId = self.test_create_recurrence(GO_TO_THE_TEMPLE_MONTHLY_RECURRENCE, user1_auth)
        PRAY_DAILY_RECURRENCE.recurrenceId = self.test_create_recurrence(PRAY_DAILY_RECURRENCE, user1_auth)
        TRIM_THE_TREES_MONTHLY_RECURRENCE.recurrenceId = self.test_create_recurrence(TRIM_THE_TREES_MONTHLY_RECURRENCE, user1_auth)
        GO_TO_CLASS_MON_WED_UNTIL_CHRISTMAS_RECURRENCE.recurrenceId = self.test_create_recurrence(GO_TO_CLASS_MON_WED_UNTIL_CHRISTMAS_RECURRENCE,
                                                                                     user1_auth)
        assert(WEEKLY_MEETING_RECURRENCE.json() == self.test_get_recurrence(WEEKLY_MEETING_RECURRENCE.recurrenceId, user1_auth))
        assert(CHURCH_RECURRENCE.json() == self.test_get_recurrence(CHURCH_RECURRENCE.recurrenceId, user1_auth))
        assert(SERVE_SOMEONE_SUN_FRI_RECURRENCE.json() == self.test_get_recurrence(SERVE_SOMEONE_SUN_FRI_RECURRENCE.recurrenceId, user1_auth))
        assert(GO_TO_THE_TEMPLE_MONTHLY_RECURRENCE.json() == self.test_get_recurrence(GO_TO_THE_TEMPLE_MONTHLY_RECURRENCE.recurrenceId, user1_auth))
        assert(PRAY_DAILY_RECURRENCE.json() == self.test_get_recurrence(PRAY_DAILY_RECURRENCE.recurrenceId, user1_auth))

        # test getting eventsByDay
        start = time.time()
        events = self.event_tests.test_get_events(start, user1_auth)




