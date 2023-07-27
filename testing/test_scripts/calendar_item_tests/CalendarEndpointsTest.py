from typing import Any

from CalendarEventTests import CalendarEventTests
from ..UserEndpointsTest import UserEndpointsTest
from testing.sample_objects.Users import *
from testing.sample_objects.calendar_items.todos import *
from testing.sample_objects.calendar_items.events import *
from testing.sample_objects.calendar_items.recurrences import *
from testing.sample_objects.calendar_items.alerts import *
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
        self.calendar_event_tests.launch_tests()



        # TEST TODOS


        # TEST LINKING TODOS AND EVENTS


        # TEST RECURRENCES
        # 1. RECURRING TODOS


        # 2. RECURRING GOALS / TODOS


        # 3. RECURRING EVENTS


        # 4. RECURRING GOALS / TODOS/ EVENTS

