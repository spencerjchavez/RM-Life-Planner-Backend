from testing.test_scripts.goal_achieving_tests.DesiresTests import DesiresTests
from testing.test_scripts.goal_achieving_tests.GoalsTests import GoalsTests
from testing.test_scripts.goal_achieving_tests.PlansTests import PlansTests
from testing.test_scripts.calendar_item_tests.CalendarEventTests import CalendarEventTests
from testing.test_scripts.UserEndpointsTest import UserEndpointsTest
from testing.sample_objects.Users import *
import requests


class GoalAchievingEndpointsTest:

    def __init__(self, base_url: str):
        self.base_url = base_url

    def launch_test(self):
        user_tests = UserEndpointsTest(self.base_url)
        desire_tests = DesiresTests(self.base_url, user_tests)
        goals_tests = GoalsTests(self.base_url, user_tests, desire_tests)
        event_tests = CalendarEventTests(self.base_url, user_tests)
        plans_tests = PlansTests(self.base_url, user_tests, desire_tests, goals_tests, event_tests)

        # reset database
        print("resetting databases")
        res = requests.post("http://localhost:8000/api/testing/reset_tables")
        print("databases successfully reset")
        print("starting desires test")
        desire_tests.launch_test()
        print("passed desire test!")
        print("starting goals test")
        goals_tests.launch_test()
        print("passed goals test!")
        print("starting plans test!")
        plans_tests.launch_test()
        print("passed plans test!")
