from app.models.Desire import Desire
import requests
from app.testing.test_scripts.UserEndpointsTest import UserEndpointsTest
from app.testing.test_scripts.calendar_item_tests.CalendarEventTests import CalendarEventTests
from app.testing.test_scripts.calendar_item_tests.ToDoTests import ToDoTests
from app.testing.test_scripts.goal_achieving_tests.DesiresTests import DesiresTests
from app.testing.test_scripts.goal_achieving_tests.GoalsTests import GoalsTests

from app.models.Recurrence import Recurrence


class RecurrenceTests:

    def __init__(self, base_url: str, user_tests: UserEndpointsTest, event_tests: CalendarEventTests,
                 todo_tests: ToDoTests, goal_tests: GoalsTests, desire_tests: DesiresTests):
        self.base_url = base_url
        self.recurrence_url = base_url + "/calendar/recurrences"
        self.recurrence_put_url = self.recurrence_url + "/put"
        self.recurrence_put_dtend_url = self.recurrence_url + "/put-dtend"
        self.user_tests = user_tests
        self.event_tests = event_tests
        self.todo_tests = todo_tests
        self.goal_tests = goal_tests
        self.desire_tests = desire_tests
        self.start_date_1 = "1999-07-04"
        self.start_date_1_plus_2_days = "1999-07-06"
        self.start_date_1_plus_1_week = "1999-07-11"
        self.start_date_1_plus_1_month = "1999-08-04"
        self.start_date_1_plus_1_year = "2000-07-04"

        self.start_date_2 = "2050-04-01"
        self.start_time_1 = "05:25:00"
        self.start_time_2 = "10:10:10"

    def launch_test(self):
        print("starting recurrence test!")
        requests.post(self.base_url + "/testing/reset_tables")
        user1_auth = self.user_tests.test_register_user(USER1)
        user2_auth = self.user_tests.test_register_user(USER2)

        self.test_happy_path(user1_auth)
        self.test_create_malformed_recurrences(user1_auth)
        self.test_update_malformed_recurrences(user1_auth)
        self.test_get_recurrences_with_malformed_params(user1_auth)
        self.test_recurrence_functions_without_authentication(user1_auth, user2_auth)
        print("passed recurrence test!")

    def test_happy_path(self, authentication: Authentication):
        self.test_event_only_recurrence_happy_path(authentication)
        self.test_todo_only_recurrence_happy_path(authentication)
        self.test_goal_and_todo_recurrence_happy_path(authentication)
        self.test_recurrence_frequencies_happy_path(authentication)


    def test_event_only_recurrence_happy_path(self, authentication: Authentication):
        recurrence = Recurrence(
            userId=authentication.user_id,
            rruleString="FREQ=DAILY;INTERVAL=1",
            startDate=self.start_date_1,
            startTime=self.start_time_1,
            eventName="event recurrence",
            eventDuration=60 * 60
        )
        # start by retrieving events_in_range to register month on months_user_accessed
        _ = self.event_tests.test_get_events_in_range(self.start_date_1, authentication)
        recurrence_id = self.test_create_recurrence(recurrence, authentication)
        events = self.event_tests.test_get_events_in_range(self.start_date_1, authentication)
        assert len(events) == 1
        assert events[0]["name"] == recurrence.eventName
        # update recurrence and assert change with get
        updated_recurrence = recurrence.copy()
        updated_recurrence.eventName = "updated event recurrence"
        self.test_update_recurrence(recurrence_id, updated_recurrence, authentication)
        events = self.event_tests.test_get_events_in_range(self.start_date_1, authentication)
        assert len(events) == 1
        assert events[0]["name"] == updated_recurrence.eventName
        # delete recurrence
        self.test_delete_recurrence(recurrence_id, authentication)

    def test_todo_only_recurrence_happy_path(self, authentication: Authentication):
        recurrence = Recurrence(
            userId=authentication.user_id,
            rruleString="FREQ=WEEKLY;INTERVAL=1",
            startDate=self.start_date_1,
            startTime=self.start_time_1,
            todoName="todo recurrence",
            todoTimeframe=Recurrence.Timeframe.WEEK,
            todoHowMuchPlanned=1
        )
        recurrence_id = self.test_create_recurrence(recurrence, authentication)
        todo = self.todo_tests.test_get_todos_by_day(self.start_date_1, authentication)[0]
        assert todo["name"] == recurrence.todoName
        # update recurrence and assert change with get
        updated_recurrence = recurrence.copy()
        updated_recurrence.todoName = "updated event recurrence"
        self.test_update_recurrence(recurrence_id, updated_recurrence, authentication)
        todo = self.todo_tests.test_get_todos_by_day(self.start_date_1, authentication)[0]
        assert todo["name"] == updated_recurrence.todoName
        # delete recurrence
        self.test_delete_recurrence(recurrence_id, authentication)

    def test_goal_and_todo_recurrence_happy_path(self, authentication: Authentication):
        # setup
        desire = Desire(
            name="my desire",
            userId=authentication.user_id,
            dateCreated=self.start_date_1,
            priorityLevel=1,
            colorR=0,
            colorG=0,
            colorB=0
        )
        desire_id = self.desire_tests.test_create_desire(desire, authentication)
        recurrence = Recurrence(
            userId=authentication.user_id,
            rruleString="FREQ=WEEKLY;INTERVAL=1",
            startDate=self.start_date_1,
            startTime=self.start_time_1,
            todoName="todo",
            todoTimeframe=Recurrence.Timeframe.WEEK,
            todoHowMuchPlanned=1,
            goalName="goal recurrence",
            goalDesireId=desire_id,
            goalHowMuch=1,
            goalTimeframe=Recurrence.Timeframe.WEEK
        )
        recurrence_id = self.test_create_recurrence(recurrence, authentication)

        # test
        goal = self.goal_tests.test_get_goals(self.start_date_1, authentication)[0]
        assert goal["name"] == recurrence.goalName
        # update recurrence and assert change with get
        updated_recurrence = recurrence.copy()
        updated_recurrence.goalName = "updated event recurrence"
        self.test_update_recurrence(recurrence_id, updated_recurrence, authentication)
        goal = self.goal_tests.test_get_goals(self.start_date_1, authentication)[0]
        assert goal["name"] == updated_recurrence.goalName
        # clean up
        self.test_delete_recurrence(recurrence_id, authentication)

    def test_recurrence_frequencies_happy_path(self, authentication: Authentication):
        # test create, get, update, and delete for different rruleString
        # setup
        daily_recurrence = Recurrence(
            userId=authentication.user_id,
            rruleString="FREQ=DAILY;INTERVAL=1",
            startDate=self.start_date_1,
            startTime=self.start_time_1,
            eventName="daily recurrence",
            eventDuration=60*60
        )
        weekly_recurrence = daily_recurrence.copy()
        weekly_recurrence.eventName = "weekly recurrence"
        weekly_recurrence.rruleString = "FREQ=WEEKLY;INTERVAL=1"

        monthly_recurrence = daily_recurrence.copy()
        monthly_recurrence.eventName = "monthly recurrence"
        monthly_recurrence.rruleString = "FREQ=MONTHLY;INTERVAL=1"

        yearly_recurrence = daily_recurrence.copy()
        monthly_recurrence.eventName = "yearly recurrence"
        yearly_recurrence.rruleString = "FREQ=YEARLY;INTERVAL=1"

        sunday_friday_recurrence = daily_recurrence.copy()
        sunday_friday_recurrence.eventName = "sunday friday recurrence"
        sunday_friday_recurrence.rruleString = "FREQ=WEEKLY;INTERVAL=1;BYDAY=SU,FR"

        # test create and get daily recurrence
        recurrence_id = self.test_create_recurrence(daily_recurrence, authentication)
        events_by_days = self.event_tests.test_get_events_in_range(daily_recurrence.startDate, authentication, self.start_date_1_plus_2_days)
        assert(len(events_by_days) == 3)  # assert that 3 days have events
        # assert that each day has the correct event
        for event in events_by_days:
            assert event["name"] == daily_recurrence.eventName

        # update to weekly recurrence, check that daily recurrences were deleted and get new recurrences
        self.test_update_recurrence(recurrence_id, weekly_recurrence, authentication)
        events = self.event_tests.test_get_events_in_range(weekly_recurrence.startDate, authentication)
        assert len(events) == 1
        assert events[0]["name"] == weekly_recurrence.eventName
        events = self.event_tests.test_get_events_in_range(self.start_date_1, authentication, self.start_date_1_plus_1_week)
        assert len(events) == 2
        assert events[1]["name"] == weekly_recurrence.eventName
        assert events[1]["startTime"] == weekly_recurrence.startTime
        # check all daily events were deleted
        no_events_here = self.event_tests.test_get_events_in_range(self.start_date_1_plus_2_days, authentication)
        assert len(no_events_here) == 0
        # update to monthly recurrence and test get
        self.test_update_recurrence(recurrence_id, monthly_recurrence, authentication)
        events = self.event_tests.test_get_events_in_range(monthly_recurrence.startDate, authentication)
        assert len(events) == 1
        assert events[0]["name"] == monthly_recurrence.eventName
        events = self.event_tests.test_get_events_in_range(self.start_date_1_plus_1_month, authentication)
        assert len(events) == 1
        assert events[0]["name"] == monthly_recurrence.eventName
        # update to yearly recurrence and test get
        self.test_update_recurrence(recurrence_id, yearly_recurrence, authentication)
        events = self.event_tests.test_get_events_in_range(yearly_recurrence.startDate, authentication)
        assert len(events) == 1
        assert events[0]["name"] == yearly_recurrence.eventName
        events = self.event_tests.test_get_events_in_range(self.start_date_1_plus_1_year, authentication)
        assert len(events) == 1
        assert events[0]["name"] == yearly_recurrence.eventName

        # update to sunday and friday recurrence and test get for startInstant and 1 week after the startInstant
        self.test_update_recurrence(recurrence_id, sunday_friday_recurrence, authentication)
        events = self.event_tests.test_get_events_in_range(sunday_friday_recurrence.startDate, authentication)
        assert(len(events) == 1)
        assert(events[0]["name"] == sunday_friday_recurrence.eventName)
        events = self.event_tests.test_get_events_in_range(self.start_date_1_plus_1_week, authentication)
        assert (len(events) == 1)  # start_date_1 is a sunday
        assert events[0]["name"] == sunday_friday_recurrence.eventName
        events = self.event_tests.test_get_events_in_range(self.start_date_1_plus_2_days, authentication)
        assert (len(events) == 0)
        # clean up
        self.test_delete_recurrence(recurrence_id, authentication)

    def test_create_malformed_recurrences(self, authentication: Authentication):
        bad_recurrence = Recurrence(
            userId=authentication.user_id,
            startDate=self.start_date_1,
        )
        self.test_create_recurrence(bad_recurrence, authentication, 400) # no rrule string
        bad_recurrence.rruleString = "FREQ=DAILY;INTERVAL=1"
        bad_recurrence.eventName = "event"
        bad_recurrence.eventDescription = "description"
        self.test_create_recurrence(bad_recurrence, authentication, 400) # event missing duration
        bad_recurrence.eventDuration = 60*60
        bad_recurrence.todoName = "todo"
        bad_recurrence.todoHowMuchPlanned = 1
        self.test_create_recurrence(bad_recurrence, authentication, 400) # to-do missing timeframe
        bad_recurrence.todoHowMuchPlanned = 0
        bad_recurrence.todoTimeframe = Recurrence.Timeframe.DAY
        self.test_create_recurrence(bad_recurrence, authentication, 400)
        bad_recurrence.todoHowMuchPlanned = 1
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
            startDate=self.start_date_1,
            startTime=self.start_time_1,
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
            startDate=self.start_date_1,
            startTime=self.start_time_1,
            eventName="event recurrence",
            eventDuration=60 * 60
        )
        good_recurrence_id = self.test_create_recurrence(good_recurrence, real_authentication)
        updated_good_recurrence = good_recurrence.copy()
        updated_good_recurrence.eventName = "updated event"
        # test
        self.test_create_recurrence(good_recurrence, another_real_authentication, 401)
        self.test_update_recurrence(good_recurrence_id, updated_good_recurrence, another_real_authentication, 401)
        self.test_delete_recurrence(good_recurrence_id, another_real_authentication, 401)

    def test_create_recurrence(self, recurrence: Recurrence, authentication: Authentication,
                                expected_response_code: int = 200):
        if recurrence.userId is None:
            recurrence.userId = authentication.user_id
        res = requests.post(self.recurrence_url,
                            json=create_authenticated_request_body("recurrence", recurrence, authentication))
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            return res.json()["recurrence_id"]

    def test_get_recurrence(self, recurrence_id: int, authentication: Authentication,
                            expected_response_code: int = 200):
        res = requests.get(self.recurrence_url + "/" + str(recurrence_id),
                           json=authentication.__dict__)
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            return res.json()["recurrence"]

    def test_update_recurrence(self, recurrence_id: int, updated_recurrence: Recurrence, authentication: Authentication,
                               expected_response_code: int = 200):
        updated_recurrence.userId = authentication.user_id
        res = requests.put(self.recurrence_put_url + "/" + str(recurrence_id),
                           json=create_authenticated_request_body("updated_recurrence", updated_recurrence,
                                                                  authentication))
        compare_responses(res, expected_response_code)

    def test_delete_recurrence(self, recurrence_id: int, authentication: Authentication,
                               expected_response_code: int = 200):
        res = requests.delete(self.recurrence_url + "/" + str(recurrence_id), json=authentication.__dict__)
        compare_responses(res, expected_response_code)
