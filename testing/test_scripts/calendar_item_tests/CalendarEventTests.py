import datetime
from typing import Optional

import dateutil.relativedelta

from models.CalendarEvent import CalendarEvent
from models.Authentication import Authentication
from testing.test_scripts.UserEndpointsTest import UserEndpointsTest
from testing.sample_objects.Users import *
from testing.sample_objects.calendar_items.events import *
import requests
from testing.test_scripts.TestingHelperFunctions import *
import threading


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

        self.test_happy_path_with_user(user1_auth)
        self.test_malformed_inputs(user1_auth, user2_auth)

    def test_malformed_inputs(self, authentication: Authentication, another_authentication: Authentication):
        self.test_create_malformed_events(authentication)
        self.test_update_with_malformed_events(authentication)
        self.test_get_with_malformed_params(authentication)
        self.test_call_functions_without_authentication(authentication, another_authentication)

    def test_create_malformed_events(self, authentication: Authentication):
        self.test_create_event(None, authentication, 500)
        event = CalendarEvent()
        self.test_create_event(event, authentication, 400)
        event.name = "aoaeu"
        event.endInstant = 50
        event.userId = authentication.user_id
        self.test_create_event(event, authentication, 400) # missing startInstant
        event.startInstant = 0
        event.linkedGoalId = -1  # doesn't exist
        self.test_create_event(event, authentication, 400)
        event.linkedGoalId = None
        event.linkedTodoId = -1  # also doesn't exist
        self.test_create_event(event, authentication, 400)
        event.linkedTodoId = None
        event.startInstant = 1000  # after endInstant
        self.test_create_event(event, authentication, 400)

    def test_get_with_malformed_params(self, authentication: Authentication):
        event = GO_TO_STORE_EVENT
        event.userId = authentication.user_id
        event_id = self.test_create_event(event, authentication)

        self.test_get_event(-1, authentication, 400)
        self.test_get_event(None, authentication, 400)
        self.test_get_events(None, authentication, 400)
        self.test_get_events(0, -40, authentication, 400)  # days out of range

    def test_update_with_malformed_events(self, authentication: Authentication):
        # set up
        good_event = GO_TO_STORE_EVENT
        good_event.userId = authentication.user_id
        event_id = self.test_create_event(good_event, authentication)
        # test
        bad_event = CalendarEvent()
        bad_event.eventId = event_id
        bad_event.userId = authentication.user_id
        self.test_update_event(event_id, bad_event, authentication, 400)
        bad_event.name = "still not a proper event"
        self.test_update_event(event_id, bad_event, authentication, 400)
        bad_event.startInstant = 0
        self.test_update_event(event_id, bad_event, authentication, 400)
        bad_event.endInstant = 500
        good_event = bad_event
        # now it should work
        self.test_update_event(event_id, good_event, authentication, 200)
        bad_event.linkedGoalId = -1
        # and now it shouldn't
        self.test_update_event(event_id, bad_event, authentication, 400)

        # clean up
        self.test_delete_event(event_id, authentication)

    def test_call_functions_without_authentication(self, real_authentication: Authentication, another_real_authentication: Authentication):
        fake_authentication = Authentication(user_id=1, api_key="951atne5u1a65ai1fd45yp5ied")
        event = GO_TO_STORE_EVENT
        event.userId = fake_authentication.user_id
        self.test_create_event(event, fake_authentication, 401)
        self.test_get_event(1, fake_authentication, 401)
        self.test_get_events(10000, fake_authentication, 401)
        self.test_update_event(1, GO_TO_STORE_EVENT, fake_authentication, 404)
        self.test_delete_event(1, fake_authentication, 401)

        # now test with real data using real authentication for another user
        event.userId = real_authentication.user_id
        real_event_id = self.test_create_event(event, real_authentication)
        self.test_get_event(real_event_id, another_real_authentication, 401)
        self.test_update_event(real_event_id, event, another_real_authentication, 401)
        self.test_delete_event(real_event_id, another_real_authentication, 401)

    def test_happy_path_with_user(self, authentication: Authentication):
        # create, get, update and delete happy path 30-min long events
        start_time_1 = datetime.datetime(year=1999, month=7, day=4)
        start_time_2 = (start_time_1 + dateutil.relativedelta.relativedelta(years=1, months=1, days=2, hours=10, minutes=5))

        # get events by day, should return nothing
        events = self.test_get_events(start_time_1.timestamp(), authentication)
        assert(len(events) == 0)

        # create events
        half_hour_events = []
        for i in range(0, 50):
            event = CalendarEvent(
                name="event" + str(i),
                description="this is the description i have written, it is rather long, but not too long. hopefully it doesn't take too long to insert all these letters into the database!!! I'm sure it won't be a problem though. All is well in the world.",
                startInstant=start_time_1.timestamp(),
                endInstant=(start_time_1 + datetime.timedelta(minutes=30)).timestamp(),
                userId=authentication.user_id
            )
            event.eventId = self.test_create_event(event, authentication)
            half_hour_events.append(event)

        for event in half_hour_events:
            event_received = self.test_get_event(event.eventId, authentication)
            assert(event.dict() == event_received.dict())

        events_received = self.test_get_events(start_time_1.timestamp(), authentication)[start_time_1.timestamp()]
        for event in half_hour_events:
            assert(events_received.index(event) >= 0)

        # update event startInstants
        for event in half_hour_events:
            new_event = event
            new_event.startInstant = start_time_2.timestamp()
            new_event.endInstant = (start_time_2 + datetime.timedelta(minutes=30)).timestamp()
            self.test_update_event(event.eventId, new_event, authentication)

        assert(len(self.test_get_events(start_time_2.timestamp(), authentication)[start_time_2.timestamp()]) == len(half_hour_events))

        # delete events
        for event in half_hour_events:
            self.test_delete_event(event.eventId, authentication)

        # assert that delete functioned correctly
        for event in half_hour_events:
            self.test_get_event(event.eventId, authentication, 404)

        # create happy path 2-day long events
        two_day_long_events = []
        start_time = start_time_1
        for i in range(0, 50):
            event = CalendarEvent(
                name="event" + str(i),
                description="this is the description i have written, it is rather long, but not too long. hopefully it doesn't take too long to insert all these letters into the database!!! I'm sure it won't be a problem though. All is well in the world.",
                startInstant=start_time.timestamp(),
                endInstant=(start_time + datetime.timedelta(days=2)).timestamp(),
                userId=authentication.user_id
            )
            event.eventId = self.test_create_event(event, authentication)
            start_time += datetime.timedelta(days=1)
            two_day_long_events.append(event)

        # test get events by day
        day = start_time_1
        for _ in two_day_long_events:
            events = self.test_get_events(day.timestamp(), authentication)[day.timestamp()]
            assert(len(events) == 2)
            day += datetime.timedelta(days=1)

        events = self.test_get_events(start_time_1.timestamp(), (start_time_1 + datetime.timedelta(days=50)).timestamp(), authentication)
        assert(len(events) == 50)
        assert(len(events[start_time_1.timestamp()]) == 1)
        assert(len(events[(start_time_1 + datetime.timedelta(days=1)).timestamp()]) == 2)

        # cleanup
        for event in two_day_long_events:
            self.test_delete_event(event.eventId, authentication)


    def test_create_event(self, event: Optional[CalendarEvent], authentication: Authentication,
                          expected_response_code: int = 200):
        event.userId = authentication.user_id
        res = requests.post(self.event_url, json=create_authenticated_request_body("event", event, authentication))
        compare_responses(res, expected_response_code)
        return res.json()["event_id"]

    def test_get_event(self, event_id: Optional[int], authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.event_url + "/" + str(event_id),
                           json=authentication.json())
        compare_responses(res, expected_response_code)
        return res.json()["event"]

    def test_get_events(self, start_day: Optional[float], authentication: Authentication,
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
