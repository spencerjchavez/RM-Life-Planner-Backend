from typing import Any

from CalendarEventTests import CalendarEventTests
from ..UserEndpointsTest import UserEndpointsTest
import requests
from ToDoTests import ToDoTests
from RecurrenceTests import RecurrenceTests


class CalendarEndpointsTest:

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.calendar_events_url = base_url + "/calendar/events"
        self.todos_url = base_url + "/calendar/todos"
        self.recurrences_url = base_url + "/calendar/recurrences"
        self.alerts_url = base_url + "/calendar/alerts"

        self.user_tests = UserEndpointsTest(base_url)
        self.calendar_event_tests = CalendarEventTests(self.base_url, self.user_tests)
        self.todo_tests = ToDoTests(self.todos_url)
        self.recurrence_tests = RecurrenceTests(self.recurrences_url)
        # self.alert_tests = AlertTests(self.alerts_url)

    def launch_test(self):
        # TEST CALENDAR EVENTS
        print("starting calendar events test")
        self.calendar_event_tests.launch_test()
        print("passed calendar events test!")
        print("starting todo test")
        self.todo_tests.launch_test()
        print("passed todo test!")
        print("starting recurrence test!")
        self.recurrence_tests.launch_test()
        print("passed recurrence test!")