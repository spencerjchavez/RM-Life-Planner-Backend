
from testing.test_scripts.calendar_item_tests.CalendarEventTests import CalendarEventTests
from testing.test_scripts.goal_achieving_tests.GoalsTests import GoalsTests
from testing.test_scripts.goal_achieving_tests.DesiresTests import DesiresTests
from ..UserEndpointsTest import UserEndpointsTest
from testing.test_scripts.calendar_item_tests.ToDoTests import ToDoTests
from testing.test_scripts.calendar_item_tests.RecurrenceTests import RecurrenceTests


class CalendarEndpointsTest:

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.calendar_events_url = base_url + "/calendar/events"
        self.todos_url = base_url + "/calendar/todos"
        self.recurrences_url = base_url + "/calendar/recurrences"
        self.alerts_url = base_url + "/calendar/alerts"

        self.user_tests = UserEndpointsTest(base_url)
        self.desire_tests = DesiresTests(base_url, self.user_tests)
        self.goal_tests = GoalsTests(base_url, self.user_tests, self.desire_tests)
        self.todo_tests = ToDoTests(self.base_url, self.desire_tests, self.goal_tests)
        self.calendar_event_tests = CalendarEventTests(self.base_url, self.user_tests, self.desire_tests, self.goal_tests, self.todo_tests)
        self.recurrence_tests = RecurrenceTests(self.base_url, self.user_tests, self.calendar_event_tests, self.todo_tests, self.goal_tests, self.desire_tests)
        # self.alert_tests = AlertTests(self.alerts_url)

    def launch_test(self):
        self.calendar_event_tests.launch_test()
        self.todo_tests.launch_test()
        self.recurrence_tests.launch_test()
