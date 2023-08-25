import dateutil.relativedelta

from models.Desire import Desire
import requests
from testing.test_scripts.TestingHelperFunctions import *
from testing.test_scripts.UserEndpointsTest import UserEndpointsTest
from testing.test_scripts.calendar_item_tests.CalendarEventTests import CalendarEventTests
from testing.test_scripts.calendar_item_tests.ToDoTests import ToDoTests
from testing.test_scripts.goal_achieving_tests.DesiresTests import DesiresTests
from testing.test_scripts.goal_achieving_tests.GoalsTests import GoalsTests

from testing.sample_objects.Users import *
from testing.sample_objects.calendar_items.recurrences import *


class RecurrenceTests:

    def __init__(self, recurrence_url: str, user_tests: UserEndpointsTest, event_tests: CalendarEventTests,
                 todo_tests: ToDoTests, goal_tests: GoalsTests, desire_tests: DesiresTests):
        self.recurrence_url = recurrence_url
        self.user_tests = user_tests
        self.event_tests = event_tests
        self.todo_tests = todo_tests
        self.goal_tests = goal_tests
        self.desire_tests = desire_tests
        self.start_time_1 = datetime.datetime(year=1999, month=7, day=4)
        self.start_time_2 = self.start_time_1 + datetime.timedelta(days=60)

    def launch_test(self):
        user1_auth = self.user_tests.test_register_user(USER1)
        user2_auth = self.user_tests.test_register_user(USER2)
        user3_auth = self.user_tests.test_register_user(USER3)

        self.test_happy_path(user1_auth)
        self.test_create_malformed_recurrences(user1_auth)
        self.test_update_malformed_recurrences(user1_auth)
        self.test_get_recurrences_with_malformed_params(user1_auth)
        self.test_recurrence_functions_without_authentication(user1_auth, user2_auth)


    def test_happy_path(self, authentication: Authentication):
        self.test_event_only_recurrence_happy_path(authentication)
        self.test_todo_only_recurrence_happy_path(authentication)
        self.test_goal_only_recurrence_happy_path(authentication)
        self.test_recurrence_frequencies_happy_path(authentication)



    def test_event_only_recurrence_happy_path(self, authentication: Authentication):
        recurrence = Recurrence(
            userId=authentication.user_id,
            rruleString="FREQ=DAILY;INTERVAL=1",
            startInstant=self.start_time_1.timestamp(),
            eventName="event recurrence",
            eventDuration=60 * 60
        )
        recurrence_id = self.test_create_recurrence(recurrence, authentication)
        event = self.event_tests.test_get_events(self.start_time_1.timestamp(), authentication)[self.start_time_1.timestamp()]
        assert event.name == recurrence.eventName
        # update recurrence and assert change with get
        updated_recurrence = recurrence
        updated_recurrence.eventName = "updated event recurrence"
        self.test_update_recurrence(recurrence_id, updated_recurrence, authentication)
        event = self.event_tests.test_get_events(self.start_time_1.timestamp(), authentication)[self.start_time_1.timestamp()]
        assert event.name == updated_recurrence.eventName
        # delete recurrence
        self.test_delete_recurrence(recurrence_id, authentication)

    def test_todo_only_recurrence_happy_path(self, authentication: Authentication):
        recurrence = Recurrence(
            userId=authentication.user_id,
            rruleString="FREQ=WEEKLY;INTERVAL=1",
            startInstant=self.start_time_1.timestamp(),
            todoName="todo recurrence",
            todoTimeframe=Recurrence.Timeframe.WEEK
        )
        recurrence_id = self.test_create_recurrence(recurrence, authentication)
        todo = self.todo_tests.test_get_todos(self.start_time_1.timestamp(), authentication)[
            self.start_time_1.timestamp()][0]
        assert todo["name"] == recurrence.todoName
        # update recurrence and assert change with get
        updated_recurrence = recurrence
        updated_recurrence.todoName = "updated event recurrence"
        self.test_update_recurrence(recurrence_id, updated_recurrence, authentication)
        todo = self.todo_tests.test_get_todos(self.start_time_1.timestamp(), authentication)[
            self.start_time_1.timestamp()][0]
        assert todo["name"] == updated_recurrence.todoName
        # delete recurrence
        self.test_delete_recurrence(recurrence_id, authentication)

    def test_goal_only_recurrence_happy_path(self, authentication: Authentication):
        # setup
        desire = Desire(
            name = "my desire",
            userId = authentication.user_id,
            dateCreated = time.time(),
            priorityLevel = 1,
            colorR = 0,
            colorG = 0,
            colorB = 0
        )
        desire_id = self.desire_tests.test_create_desire(desire, authentication)
        recurrence = Recurrence(
            userId=authentication.user_id,
            rruleString="FREQ=WEEKLY;INTERVAL=1",
            startInstant=self.start_time_1.timestamp(),
            goalName="todo recurrence",
            goalDesireId=desire_id,
            goalHowMuch=1,
            goalTimeframe=Recurrence.Timeframe.WEEK
        )
        recurrence_id = self.test_create_recurrence(recurrence, authentication)

        # test
        goal = self.goal_tests.test_get_goals(self.start_time_1.timestamp(), authentication)[
            self.start_time_1.timestamp()][0]
        assert goal["name"] == recurrence.goalName
        # update recurrence and assert change with get
        updated_recurrence = recurrence
        updated_recurrence.goalName = "updated event recurrence"
        self.test_update_recurrence(recurrence_id, updated_recurrence, authentication)
        goal = self.goal_tests.test_get_goals(self.start_time_1.timestamp(), authentication)[
            self.start_time_1.timestamp()][0]
        assert goal["name"] == updated_recurrence.goalName
        # clean up
        self.test_delete_recurrence(recurrence_id, authentication)

    def test_recurrence_frequencies_happy_path(self, authentication: Authentication):
        # test create, get, update, and delete for different rruleString
        # setup
        daily_recurrence = Recurrence(
            userId = authentication.user_id,
            rruleString = "FREQ=DAILY;INTERVAL=1",
            startInstant = self.start_time_1.timestamp(),
            eventName = "daily recurrence",
            eventDuration = 60*60
        )
        weekly_recurrence = daily_recurrence
        weekly_recurrence.eventName = "weekly recurrence"
        weekly_recurrence.rruleString = "FREQ=WEEKLY;INTERVAL=1"

        monthly_recurrence = daily_recurrence
        monthly_recurrence.eventName = "monthly recurrence"
        monthly_recurrence.rruleString = "FREQ=MONTHLY;INTERVAL=1"

        yearly_recurrence = daily_recurrence
        monthly_recurrence.eventName = "yearly recurrence"
        yearly_recurrence.rruleString = "FREQ=YEARLY;INTERVAL=1"

        sunday_friday_recurrence = daily_recurrence
        sunday_friday_recurrence.eventName = "sunday friday recurrence"
        sunday_friday_recurrence.rruleString = "FREQ=WEEKLY;INTERVAL=1;BYDAY=SU,FR",

        # test create and get daily recurrence
        recurrence_id = self.test_create_recurrence(daily_recurrence, authentication)
        events_by_days = self.event_tests.test_get_events(daily_recurrence.startInstant, daily_recurrence.startInstant + datetime.timedelta(days=2).total_seconds(), authentication)
        assert(len(events_by_days) == 3)  # assert that 3 days have events
        # assert that each day has the correct event
        for events_in_day in events_by_days.keys():
            assert events_in_day[0]["name"] == daily_recurrence.eventName

        # update to weekly recurrence, check that daily recurrences were deleted and get new recurrences
        self.test_update_recurrence(recurrence_id, weekly_recurrence, authentication)
        events = self.event_tests.test_get_events(weekly_recurrence.startInstant, authentication)
        assert len(events) == 1
        assert events[0]["name"] == weekly_recurrence.eventName
        events = self.event_tests.test_get_events((datetime.datetime.fromtimestamp(yearly_recurrence.startInstant) + dateutil.relativedelta.relativedelta(weeks=1)).timestamp(), authentication)
        assert len(events) == 1
        assert events[0]["name"] == yearly_recurrence.eventName
        # check all daily events were deleted
        no_events_here = self.event_tests.test_get_events(weekly_recurrence.startInstant + datetime.timedelta(days=2).total_seconds(), authentication)
        assert len(no_events_here) == 0
        # update to monthly recurrence and test get
        self.test_update_recurrence(recurrence_id, monthly_recurrence, authentication)
        events = self.event_tests.test_get_events(monthly_recurrence.startInstant, authentication)
        assert len(events) == 1
        assert events[0]["name"] == monthly_recurrence.eventName
        events = self.event_tests.test_get_events((datetime.datetime.fromtimestamp(yearly_recurrence.startInstant) + dateutil.relativedelta.relativedelta(months=1)).timestamp(), authentication)
        assert len(events) == 1
        assert events[0]["name"] == yearly_recurrence.eventName
        # update to yearly recurrence and test get
        self.test_update_recurrence(recurrence_id, yearly_recurrence, authentication)
        events = self.event_tests.test_get_events(yearly_recurrence.startInstant, authentication)
        assert len(events) == 1
        assert events[0]["name"] == yearly_recurrence.eventName
        events = self.event_tests.test_get_events((datetime.datetime.fromtimestamp(yearly_recurrence.startInstant) + dateutil.relativedelta.relativedelta(years=1)).timestamp(), authentication)
        assert len(events) == 1
        assert events[0]["name"] == yearly_recurrence.eventName

        # update to sunday and friday recurrence and test get for startInstant and 1 week after the startInstant
        self.test_update_recurrence(recurrence_id, sunday_friday_recurrence, authentication)
        events = self.event_tests.test_get_events(sunday_friday_recurrence.startInstant, authentication)
        assert(len(events) == 1)
        assert(events[0]["name"] == sunday_friday_recurrence.eventName)
        events = self.event_tests.test_get_events((datetime.datetime.fromtimestamp(sunday_friday_recurrence.startInstant) + datetime.timedelta(weeks=1)).timestamp(), authentication)
        assert (len(events) == 1)
        assert events[0]["name"] == sunday_friday_recurrence.eventName
        # clean up
        self.test_delete_recurrence(recurrence_id, authentication)

    def test_create_malformed_recurrences(self, authentication: Authentication):
        bad_recurrence = Recurrence(
            userId=authentication.user_id,
            startInstant=self.start_time_1.timestamp(),
        )
        self.test_create_recurrence(bad_recurrence, authentication, 400) # no rrule string
        bad_recurrence.rruleString = "FREQ=DAILY;INTERVAL=1"
        bad_recurrence.eventName = "event"
        bad_recurrence.eventDescription = "description"
        self.test_create_recurrence(bad_recurrence, authentication, 400) # event missing duration
        bad_recurrence.eventDuration = 60*60
        bad_recurrence.todoName = "todo"
        self.test_create_recurrence(bad_recurrence, authentication, 400) # to-do missing timeframe
        bad_recurrence.todoTimeframe = Recurrence.Timeframe.DAY
        bad_recurrence.goalName = "goal"
        self.test_create_recurrence(bad_recurrence, authentication, 400) # goal missing howMuch + timeframe
        bad_recurrence.goalTimeframe = Recurrence.Timeframe.DAY
        self.test_create_recurrence(bad_recurrence, authentication, 400) # goal missing howMuch
        bad_recurrence.goalHowMuch = 1
        bad_recurrence.goalTimeframe = Recurrence.Timeframe.WEEK
        self.test_create_recurrence(bad_recurrence, authentication, 400) # goal has different timeframe than to_do

    def test_update_malformed_recurrences(self, authentication: Authentication):
        # set up
        good_recurrence = Recurrence(
            userId=authentication.user_id,
            rruleString="FREQ=DAILY;INTERVAL=1",
            startInstant=self.start_time_1.timestamp(),
            eventName="event recurrence",
            eventDuration=60 * 60
        )
        good_recurrence_id = self.test_create_recurrence(good_recurrence, authentication)
        bad_recurrence = good_recurrence
        bad_recurrence.eventDuration = None
        self.test_update_recurrence(good_recurrence_id, bad_recurrence, authentication, 400)
        bad_recurrence.eventDuration = 60 * 60
        bad_recurrence.todoName = "todo"
        self.test_update_recurrence(good_recurrence_id, bad_recurrence, authentication, 400)  # to-do missing timeframe
        bad_recurrence.todoTimeframe = Recurrence.Timeframe.DAY
        bad_recurrence.goalName = "goal"
        self.test_update_recurrence(good_recurrence_id, bad_recurrence, authentication, 400)  # goal missing howMuch + timeframe
        bad_recurrence.goalTimeframe = Recurrence.Timeframe.DAY
        self.test_update_recurrence(good_recurrence_id, bad_recurrence, authentication, 400)  # goal missing howMuch
        bad_recurrence.goalHowMuch = 1
        bad_recurrence.goalTimeframe = Recurrence.Timeframe.WEEK
        self.test_update_recurrence(good_recurrence_id, bad_recurrence, authentication, 400)  # goal has different timeframe than to_do
        # clean up
        self.test_delete_recurrence(good_recurrence_id, authentication)

    def test_get_recurrences_with_malformed_params(self, authentication: Authentication):
        self.test_get_recurrence(10, authentication, 404)

    def test_recurrence_functions_without_authentication(self, real_authentication: Authentication, another_real_authentication: Authentication):
        # setup
        good_recurrence = Recurrence(
            userId=real_authentication.user_id,
            rruleString="FREQ=DAILY;INTERVAL=1",
            startInstant=self.start_time_1.timestamp(),
            eventName="event recurrence",
            eventDuration=60 * 60
        )
        good_recurrence_id = self.test_create_recurrence(good_recurrence, real_authentication)
        updated_good_recurrence = good_recurrence
        updated_good_recurrence.eventName = "updated event"
        # test
        self.test_create_recurrence(good_recurrence, another_real_authentication, 401)
        self.test_update_recurrence(good_recurrence_id, updated_good_recurrence, another_real_authentication, 401)
        self.test_delete_recurrence(good_recurrence_id, another_real_authentication, 401)

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
                           json=authentication.__dict__)
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
        res = requests.delete(self.recurrence_url + "/" + str(recurrence_id), json=authentication.__dict__)
        compare_responses(res, expected_response_code)
