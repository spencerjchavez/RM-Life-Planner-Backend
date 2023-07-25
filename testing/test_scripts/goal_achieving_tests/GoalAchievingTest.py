from testing.test_scripts.goal_achieving_tests.ActionsTests import ActionsTests
from testing.test_scripts.goal_achieving_tests.DesiresTests import DesiresTests
from testing.test_scripts.goal_achieving_tests.GoalsTests import GoalsTests
from testing.test_scripts.goal_achieving_tests.PlansTests import PlansTests
from testing.test_scripts.UserEndpointsTest import UserEndpointsTest
from testing.sample_objects.Users import *
from testing.sample_objects.goal_achieving.desires import *
from testing.sample_objects.goal_achieving.goals import *
from testing.sample_objects.goal_achieving.plans import *
from testing.sample_objects.goal_achieving.actions import *
import requests


class GoalAchievingEndpointsTest:

    def __init__(self, base_url: str):
        self.base_url = base_url

        self.desires_url = base_url + "/desires"
        self.goals_url = base_url + "/goals"
        self.plans_url = base_url + "/plans"
        self.actions_url = base_url + "/actions"

    def launch_test(self):
        desire_tests = DesiresTests(self.desires_url)
        goals_tests = GoalsTests(self.goals_url)
        plans_tests = PlansTests(self.plans_url)
        action_tests = ActionsTests(self.actions_url)
        user_tests = UserEndpointsTest(self.base_url)

        # reset database
        print("resetting databases")
        res = requests.post("http://localhost:8000/api/testing/reset_tables")
        print("databases successfully reset")

        # init user to start
        USER1_AUTH = user_tests.test_register_user(USER1)

        # test create desire
        DESIRE1.desireId = desire_tests.test_create_desire(DESIRE1, USER1_AUTH)

        # test get desire
        DESIRE1_dict = desire_tests.test_get_desire(DESIRE1.desireId, USER1_AUTH)
        if DESIRE1_dict != DESIRE1.json():
            raise ValueError(f"desire retrieved is not equivalent to desire created!!\n{DESIRE1_dict} != {DESIRE1.__dict__}")

        # test update desire
        desire_tests.test_update_desire(DESIRE1.desireId, DESIRE2, USER1_AUTH)
        DESIRE1_dict = desire_tests.test_get_desire(DESIRE1.desireId, USER1_AUTH)
        DESIRE2.desireId = DESIRE1.desireId
        if DESIRE1_dict != DESIRE2:
            raise ValueError(f"Desire not updated properly! !!\n{DESIRE1_dict} != {DESIRE1.__dict__}")

        # test delete desire
        desire_tests.test_delete_desire(DESIRE1.desireId, USER1_AUTH)
        desire_tests.test_get_desire(DESIRE1.desireId, USER1_AUTH, 404)
