from typing import Optional

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
        print("starting event tests")
        print("resetting the database")
        requests.post(self.base_url + "/testing/reset_tables")
        print("databases successfully reset")

        user1_auth = self.user_tests.test_register_user(USER1)
        user2_auth = self.user_tests.test_register_user(USER2)
        user3_auth = self.user_tests.test_register_user(USER3)

        DO_HOMEWORK_EVENT.userId = user1_auth.user_id
        DO_HOMEWORK_EVENT.eventId = self.test_create_event(DO_HOMEWORK_EVENT, user1_auth)
        res = self.test_get_event(DO_HOMEWORK_EVENT.eventId, user1_auth)
        assert(DO_HOMEWORK_EVENT == res)

        GO_TO_STORE_EVENT.userId = user1_auth.user_id
        GO_TO_STORE_EVENT.eventId = self.test_create_event(GO_TO_STORE_EVENT, user1_auth)
        res = self.test_get_event(GO_TO_STORE_EVENT.eventId, user1_auth)
        assert(GO_TO_STORE_EVENT == res)

        READ_SCRIPTURES_EVENT.userId = user1_auth.user_id
        READ_SCRIPTURES_EVENT.eventId = self.test_create_event(READ_SCRIPTURES_EVENT, user1_auth)
        res = self.test_get_event(READ_SCRIPTURES_EVENT.eventId, user1_auth)
        assert(READ_SCRIPTURES_EVENT == res)

        APPLY_FOR_JOB_EVENT.userId = user1_auth.user_id
        APPLY_FOR_JOB_EVENT.eventId = self.test_create_event(APPLY_FOR_JOB_EVENT, user1_auth)
        res = self.test_get_event(APPLY_FOR_JOB_EVENT.eventId, user1_auth)
        assert (APPLY_FOR_JOB_EVENT == res)

        WEEK_LONG_VACATION_EVENT.userId = user1_auth.user_id
        WEEK_LONG_VACATION_EVENT.eventId = self.test_create_event(WEEK_LONG_VACATION_EVENT, user1_auth)
        res = self.test_get_event(WEEK_LONG_VACATION_EVENT.eventId, user1_auth)
        assert (WEEK_LONG_VACATION_EVENT == res)

        NEW_NAME = "new event name"
        NEW_DESCRIPTION = "ahhhhhhhhhh!!!!!!!!!!!!!!!\nGRRRRRRRRRRRRRR\n happy happy happy happy joy joy joy what da heck"
        DO_HOMEWORK_EVENT.name = NEW_NAME
        DO_HOMEWORK_EVENT.description = NEW_DESCRIPTION
        DO_HOMEWORK_EVENT.endInstant = datetime.datetime.now() + datetime.timedelta(hours=5)
        self.test_update_event(DO_HOMEWORK_EVENT.eventId, DO_HOMEWORK_EVENT, user1_auth)
        res = self.test_get_event(DO_HOMEWORK_EVENT.eventId, user1_auth)
        assert(DO_HOMEWORK_EVENT == res)

        NEW_NAME = "new event name"
        NEW_DESCRIPTION = "ahhhhhhhhhh!!!!!!!!!!!!!!!\nGRRRRRRRRRRRRRR\n happy happy happy happy joy joy joy what da heck"
        DO_HOMEWORK_EVENT.name = NEW_NAME
        DO_HOMEWORK_EVENT.description = NEW_DESCRIPTION
        DO_HOMEWORK_EVENT.endInstant = datetime.datetime.now() + datetime.timedelta(hours=5)
        self.test_update_event(DO_HOMEWORK_EVENT.eventId, DO_HOMEWORK_EVENT, user1_auth)
        res = self.test_get_event(DO_HOMEWORK_EVENT.eventId, user1_auth)
        assert(DO_HOMEWORK_EVENT == res)

        NEW_NAME = "new event name"
        NEW_DESCRIPTION = "ahhhhhhhhhh!!!!!!!!!!!!!!!\nGRRRRRRRRRRRRRR\n happy happy happy happy joy joy joy what da heck"
        GO_TO_STORE_EVENT.name = NEW_NAME
        GO_TO_STORE_EVENT.description = NEW_DESCRIPTION
        GO_TO_STORE_EVENT.endInstant = datetime.datetime.now() + datetime.timedelta(hours=5)
        self.test_update_event(GO_TO_STORE_EVENT.eventId, GO_TO_STORE_EVENT, user1_auth)
        res = self.test_get_event(GO_TO_STORE_EVENT.eventId, user1_auth)
        assert(GO_TO_STORE_EVENT == res)

        NEW_NAME = "new event name"
        NEW_DESCRIPTION = "ahhhhhhhhhh!!!!!!!!!!!!!!!\nGRRRRRRRRRRRRRR\n happy happy happy happy joy joy joy what da heck"
        READ_SCRIPTURES_EVENT.name = NEW_NAME
        READ_SCRIPTURES_EVENT.description = NEW_DESCRIPTION
        READ_SCRIPTURES_EVENT.endInstant = datetime.datetime.now() + datetime.timedelta(hours=5)
        self.test_update_event(READ_SCRIPTURES_EVENT.eventId, READ_SCRIPTURES_EVENT, user1_auth)
        res = self.test_get_event(READ_SCRIPTURES_EVENT.eventId, user1_auth)
        assert(READ_SCRIPTURES_EVENT == res)

        self.test_delete_event(READ_SCRIPTURES_EVENT.eventId, user1_auth)
        self.test_get_event(READ_SCRIPTURES_EVENT.eventId, user1_auth, 404)
        READ_SCRIPTURES_EVENT.eventId = self.test_create_event(READ_SCRIPTURES_EVENT, user1_auth)
        self.test_create_event(READ_SCRIPTURES_EVENT, user2_auth, 401)

        events_list: list = self.test_get_events(time.time(), user1_auth)
        assert (len(events_list) == 5)
        assert (events_list.index(GO_TO_STORE_EVENT.dict()))
        assert (events_list.index(READ_SCRIPTURES_EVENT.dict()))
        assert (events_list.index(APPLY_FOR_JOB_EVENT.dict()))
        assert (events_list.index(GO_TO_STORE_EVENT.dict()))
        assert (events_list.index(WEEK_LONG_VACATION_EVENT.dict()))  # check that READ_SCRIPTURES_EVENT exists within the list

        events_tomorrow_list = self.test_get_events((datetime.datetime.now() + datetime.timedelta(days=1)).timestamp())
        assert (len(events_tomorrow_list) == 1)
        assert (WEEK_LONG_VACATION_EVENT.dict() == events_tomorrow_list[0])

        READ_SCRIPTURES_EVENT.userId = user2_auth.user_id
        READ_SCRIPTURES_EVENT.eventId = self.test_create_event(READ_SCRIPTURES_EVENT, user2_auth)

        READ_SCRIPTURES_EVENT.userId = user3_auth.user_id
        READ_SCRIPTURES_EVENT.eventId = self.test_create_event(READ_SCRIPTURES_EVENT, user3_auth)


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
        return res.json()["event"]

    def test_get_events(self, start_day: float, authentication: Authentication,
                            expected_response_code: int = 200):
        res = requests.get(self.event_url, params={"start_day": start_day}, json=authentication.json())
        compare_responses(res, expected_response_code)
        return res.json()["events"]

    def test_get_events(self, start_day: float, end_day: float, authentication: Authentication,
                            expected_response_code: int = 200):
        res = requests.get(self.event_url, params={"start_day": start_day, 'end_day': end_day}, json=authentication.json())
        compare_responses(res, expected_response_code)
        return res.json()["events"]

    def test_update_event(self, event_id: int, updated_event: CalendarEvent, authentication: Authentication,
                          expected_response_code: int = 200):
        updated_event.userId = authentication.user_id
        res = requests.put(self.event_url + "/" + str(event_id),
                           json=create_authenticated_request_body("updated_event", updated_event, authentication))
        compare_responses(res, expected_response_code)

    def test_delete_event(self, event_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.delete(self.event_url + "/" + str(event_id), json=authentication.json())
        compare_responses(res, expected_response_code)
