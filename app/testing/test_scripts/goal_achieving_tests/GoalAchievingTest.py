from app.testing.test_scripts.goal_achieving_tests.DesiresTests import DesiresTests
from app.testing.test_scripts.goal_achieving_tests.GoalsTests import GoalsTests
from app.testing.test_scripts.UserEndpointsTest import UserEndpointsTest


class GoalAchievingEndpointsTest:

    def __init__(self, base_url: str):
        self.base_url = base_url

    def launch_test(self):
        user_tests = UserEndpointsTest(self.base_url)
        desire_tests = DesiresTests(self.base_url, user_tests)
        goals_tests = GoalsTests(self.base_url, user_tests, desire_tests)

        # reset database
        desire_tests.launch_test()
        goals_tests.launch_test()
