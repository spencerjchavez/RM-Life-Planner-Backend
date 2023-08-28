from typing import Optional

from app.models.CalendarEvent import CalendarEvent
from app.models.Desire import Desire
from app.models.Goal import Goal
from app.models.ToDo import ToDo
from app.testing.test_scripts.UserEndpointsTest import UserEndpointsTest
import requests
from app.testing.test_scripts.calendar_item_tests.ToDoTests import ToDoTests
from app.testing.test_scripts.goal_achieving_tests.DesiresTests import DesiresTests
from app.testing.test_scripts.goal_achieving_tests.GoalsTests import GoalsTests


class CalendarEventTests:

    def __init__(self, base_url: str, user_tests: UserEndpointsTest, desire_tests: DesiresTests, goal_tests: GoalsTests, todo_tests: ToDoTests):
        self.event_url = base_url + "/calendar/events"
        self.get_event_by_event_id = self.event_url + "/by-event-id"
        self.get_events_by_days_list_url = self.event_url + "/in-date-list"
        self.get_events_by_days_range_url = self.event_url + "/in-date-range"
        self.base_url = base_url
        self.user_tests = user_tests
        self.desire_tests = desire_tests
        self.goal_tests = goal_tests
        self.todo_tests = todo_tests
        self.start_date1 = "1999-07-04"
        self.start_date2 = "2000-12-24"
        self.start_time1 = "12:30:55"
        self.start_time2 = "15:59:00"
        self.bad_date = "1999-77-04"
        self.bad_time = "500:15:00"

    def launch_test(self):
        print("starting calendar events test")
        requests.post(self.base_url + "/testing/reset_tables")
        user1_auth = self.user_tests.test_register_user(USER1)
        user2_auth = self.user_tests.test_register_user(USER2)

        desire = Desire(
            name="my desire",
            userId=user1_auth.user_id,
            dateCreated="2010-08-15",
            priorityLevel=1,
            colorR=0,
            colorG=0,
            colorB=0
        )
        desire_id = self.desire_tests.test_create_desire(desire, user1_auth)
        goal = Goal(
            desireId=desire_id,
            userId=user1_auth.user_id,
            name="my goal",
            howMuch=1,
            startDate=self.start_date1
        )
        goal_id = self.goal_tests.test_create_goal(goal, user1_auth)
        todo = ToDo(
            name="go to the store today",
            startDate=self.start_date1,
            deadlineDate=self.start_date1,
            userId=user1_auth.user_id,
            linkedGoalId=goal_id,
            howMuchPlanned=1
        )
        todo_id = self.todo_tests.test_create_todo(todo, user1_auth)
        # test
        self.test_happy_path_with_user(user1_auth, todo_id, goal_id)
        self.test_malformed_inputs(user1_auth, user2_auth)
        # cleanup
        self.todo_tests.test_delete_todo(todo_id, user1_auth)
        self.goal_tests.test_delete_goal(goal_id, user1_auth)
        self.desire_tests.test_delete_desire(desire_id, user1_auth)
        print("passed calendar events test!")

    def test_malformed_inputs(self, authentication: Authentication, another_authentication: Authentication):
        self.test_create_malformed_events(authentication)
        self.test_update_with_malformed_events(authentication)
        self.test_get_with_malformed_params(authentication)
        self.test_call_functions_without_authentication(authentication, another_authentication)

    def test_create_malformed_events(self, authentication: Authentication):
        event = CalendarEvent()
        self.test_create_event(event, authentication, 400)
        event.name = "aoaeu"
        event.endDate = self.start_date1
        event.endTime = self.start_time2
        event.userId = authentication.user_id
        self.test_create_event(event, authentication, 400) # missing start date and time
        event.startDate = self.start_date1
        self.test_create_event(event, authentication, 400) # missing start time
        event.startTime = self.start_time1
        event.linkedTodoId = -1  # doesn't exist
        self.test_create_event(event, authentication, 404)
        event.linkedTodoId = None
        event.startDate = self.start_date2  # after endInstant
        self.test_create_event(event, authentication, 400)
        event.startDate = self.start_date1
        event.howMuchAccomplished = 1
        self.test_create_event(event, authentication, 400)

    def test_get_with_malformed_params(self, authentication: Authentication):
        self.test_get_event(-1, authentication, 404)
        self.test_get_events_in_range(self.bad_date, authentication, self.bad_date, 400)  # days out of range
        self.test_get_events_in_range(self.start_date2, authentication, self.start_date1, 400)

    def test_update_with_malformed_events(self, authentication: Authentication):
        # set up
        good_event = CalendarEvent(
            name="event",
            userId=authentication.user_id,
            startDate=self.start_date1,
            startTime=self.start_time1,
            endDate=self.start_date1,
            endTime=self.start_time2
        )
        good_event.userId = authentication.user_id
        event_id = self.test_create_event(good_event, authentication)
        # test
        bad_event = CalendarEvent()
        bad_event.eventId = event_id
        bad_event.userId = authentication.user_id
        self.test_update_event(event_id, bad_event, authentication, 400)
        bad_event.name = "still not a proper event"
        self.test_update_event(event_id, bad_event, authentication, 400)
        bad_event.startTime = self.start_time2
        bad_event.endDate = self.start_date1
        bad_event.endTime = self.start_time1
        self.test_update_event(event_id, bad_event, authentication, 400)
        bad_event.startDate = self.start_date1
        self.test_update_event(event_id, bad_event, authentication, 400)
        bad_event.startTime = self.bad_time
        bad_event.endTime = self.start_time2
        self.test_update_event(event_id, bad_event, authentication, 400)
        bad_event.startTime = self.start_time1
        bad_event.linkedTodoId = -1
        self.test_update_event(event_id, bad_event, authentication, 404)
        bad_event.linkedTodoId = None
        bad_event.howMuchAccomplished = 1
        self.test_update_event(event_id, bad_event, authentication, 400)
        bad_event.howMuchAccomplished = None
        bad_event.notes = "notes"
        self.test_update_event(event_id, bad_event, authentication, 400)

        # clean up
        self.test_delete_event(event_id, authentication)

    def test_call_functions_without_authentication(self, real_authentication: Authentication, another_real_authentication: Authentication):
        # setup
        event = CalendarEvent(
            name="event",
            userId=real_authentication.user_id,
            startDate=self.start_date1,
            startTime=self.start_time1,
            endDate=self.start_date1,
            endTime=self.start_time2
        )
        event_id = self.test_create_event(event, real_authentication)
        # test
        self.test_get_event(event_id, another_real_authentication, 401)
        event.userId = another_real_authentication.user_id
        self.test_update_event(event_id, event, another_real_authentication, 401)
        self.test_delete_event(event_id, another_real_authentication, 401)
        # cleanup
        self.test_delete_event(event_id, real_authentication)

    def test_happy_path_with_user(self, authentication: Authentication, todo_id: int, goal_id: int):
        # create, get, update and delete happy path 30-min long events
        # setup
        event = CalendarEvent(
            name="event",
            description="this is the description i have written, it is rather long, but not too long. hopefully it doesn't take too long to insert all these letters into the database!!! I'm sure it won't be a problem though. All is well in the world.",
            userId=authentication.user_id,
            startDate=self.start_date1,
            startTime=self.start_time1,
            endDate=self.start_date1,
            endTime=self.start_time2,
            linkedTodoId=todo_id,
            linkedGoalId=goal_id
        )
        updated_event = event.copy()
        updated_event.name = "updated event"
        updated_event.howMuchAccomplished = 1
        #test
        # get events by day, should return nothing
        events = self.test_get_events_in_range(self.start_date1, authentication)
        assert len(events) == 0
        # test create
        event.eventId = self.test_create_event(event, authentication)
        # test update
        self.test_update_event(event.eventId, updated_event, authentication)
        event_received = self.test_get_event(event.eventId, authentication)
        assert updated_event.name == event_received["name"]
        assert updated_event.howMuchAccomplished == event_received["howMuchAccomplished"]
        # make sure the goal's deadline_date was updated too
        goal_dict = self.goal_tests.test_get_goal(event.linkedGoalId, authentication)
        assert goal_dict["deadlineDate"] == event.endDate
        # test get by day

        events_received = self.test_get_events_in_range(self.start_date1, authentication, self.start_date2)
        assert len(events_received) == 1
        assert events_received[0]["name"] == updated_event.name
        # delete events
        self.test_delete_event(event.eventId, authentication)
        # assert that delete functioned correctly
        self.test_get_event(event.eventId, authentication, 404)
        events = self.test_get_events_in_range(self.start_date1, authentication)
        assert len(events) == 0

    def test_create_event(self, event: CalendarEvent, authentication: Authentication,
                          expected_response_code: int = 200):
        event.userId = authentication.user_id
        res = requests.post(self.event_url, json=create_authenticated_request_body("event", event, authentication))
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            return res.json()["event_id"]

    def test_get_event(self, event_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.get_event_by_event_id + "/" + str(event_id),
                           json=authentication.__dict__)
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            return res.json()["event"]

    def test_get_events_in_range(self, start_day: str, authentication: Authentication, end_day: Optional[str] = None,
                            expected_response_code: int = 200):
        res = requests.get(self.get_events_by_days_range_url, params={"start_date": start_day, "end_date": end_day}, json=authentication.__dict__)
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            return res.json()["events"]

    '''
    def test_get_events(self, start_day: float, end_day: float, authentication: Authentication,
                            expected_response_code: int = 200):
        res = requests.get(self.event_url, params={"start_day": start_day, 'end_day': end_day}, json=authentication.__dict__)
        compare_responses(res, expected_response_code)
        return res.json()["events"]
    '''
    def test_update_event(self, event_id: int, updated_event: CalendarEvent, authentication: Authentication,
                          expected_response_code: int = 200):
        updated_event.userId = authentication.user_id
        res = requests.put(self.event_url + "/" + str(event_id),
                           json=create_authenticated_request_body("updated_event", updated_event, authentication))
        compare_responses(res, expected_response_code)

    def test_delete_event(self, event_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.delete(self.event_url + "/" + str(event_id), json=authentication.__dict__)
        compare_responses(res, expected_response_code)
