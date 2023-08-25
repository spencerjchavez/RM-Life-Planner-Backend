import datetime
import time
from typing import Optional

import requests
from testing.test_scripts.TestingHelperFunctions import *
from models.Goal import Goal
from models.Authentication import Authentication
from testing.test_scripts.goal_achieving_tests.DesiresTests import DesiresTests
from testing.test_scripts.UserEndpointsTest import UserEndpointsTest
from testing.sample_objects.Users import *
from models.Desire import Desire


class GoalsTests:

    def __init__(self, base_url: str, user_tests: UserEndpointsTest, desire_tests: DesiresTests):
        self.base_url = base_url
        self.goals_url = base_url + "/goals"
        self.get_goals_by_days_list = self.goals_url + "/by-days-list"
        self.get_goals_by_days_range = self.goals_url + "/by-days-range"
        self.user_tests = user_tests
        self.desire_tests = desire_tests
        self.start_time = datetime.datetime(day=4, month=7, year=1999).timestamp()
        self.start_time2 = datetime.datetime(day=5, month=8, year=1999).timestamp()

    def launch_test(self):
        print("resetting the database")
        requests.post(self.base_url + "/testing/reset_tables")
        print("databases successfully reset")
        user1_auth = self.user_tests.test_register_user(USER1)
        user2_auth = self.user_tests.test_register_user(USER2)

        # setup sample desire, goal, and event for plans to be tested with
        desire = Desire(
            name="my desire",
            userId=user1_auth.user_id,
            dateCreated=time.time(),
            priorityLevel=1,
            colorR=0,
            colorG=0,
            colorB=0
        )
        desire_id = self.desire_tests.test_create_desire(desire, user1_auth)
        # run tests
        self.test_happy_path(user1_auth, desire_id)
        self.test_malformed_inputs(user1_auth, user2_auth, desire_id)
        # cleanup
        self.desire_tests.test_delete_desire(desire_id, user1_auth)

    def test_happy_path(self, authentication: Authentication, desire_id: int):
        goal = Goal(
            desireId=desire_id,
            userId=authentication.user_id,
            name="my goal",
            howMuch=1,
            startInstant=self.start_time,
            endInstant=self.start_time + 10000
        )
        updated_goal = goal
        updated_goal.name = "updated goal"
        # test create, update, get, and delete
        goal_id = self.test_create_goal(goal, authentication)
        self.test_update_goal(goal_id, updated_goal, authentication)
        goal_retrieved = self.test_get_goal(goal_id, authentication)
        assert goal_retrieved["name"] == updated_goal.name
        # test get goals by day
        goals_retrieved = self.test_get_goals(self.start_time, authentication)[str(int(self.start_time))]
        assert len(goals_retrieved) == 1
        assert goals_retrieved[0]["name"] == updated_goal.name
        goals_retrieved = self.test_get_goals(self.start_time2, authentication)[str(int(self.start_time2))]
        assert len(goals_retrieved) == 0
        # updated startInstant and check again
        updated_goal.startInstant = self.start_time2
        updated_goal.endInstant = updated_goal.startInstant + 10000
        self.test_update_goal(goal_id, updated_goal, authentication)
        goals = self.test_get_goals(self.start_time2, authentication)[str(int(self.start_time2))]
        assert len(goals) == 1
        self.test_delete_goal(goal_id, authentication)
        # assert that delete worked
        goals_retrieved = self.test_get_goals(self.start_time2, authentication)[str(int(self.start_time2))]
        assert len(goals_retrieved) == 0

    def test_malformed_inputs(self, authentication: Authentication, another_authentication: Authentication,
                                  desire_id: int):
        self.test_create_malformed_goals(authentication, desire_id)
        self.test_update_with_malformed_goals(authentication, desire_id)
        self.test_get_with_malformed_params(authentication, desire_id)
        self.test_call_functions_without_authentication(authentication, another_authentication, desire_id)

    def test_create_malformed_goals(self, authentication: Authentication, desire_id: int):
        bad_goal = Goal(
            desireId=desire_id-1,
            userId=authentication.user_id,
            name="my goal",
            howMuch=1,
            startInstant=self.start_time
        )
        self.test_create_goal(bad_goal, authentication, 404)  # bad desireId
        bad_goal.desireId = desire_id
        bad_goal.howMuch = -1
        self.test_create_goal(bad_goal, authentication, 400)  # bad howMuch
        bad_goal.howMuch = 1
        bad_goal.name = ""
        self.test_create_goal(bad_goal, authentication, 400)  # bad goal name
        bad_goal.name = "goal"
        bad_goal.startInstant = None
        self.test_create_goal(bad_goal, authentication, 400)  # bad startInstant
        bad_goal.startInstant = self.start_time
        bad_goal.endInstant = self.start_time - 1000000
        self.test_create_goal(bad_goal, authentication, 400)  # bad endInstant

    def test_update_with_malformed_goals(self, authentication: Authentication, desire_id: int):
        # setup
        good_goal = Goal(
            desireId=desire_id,
            userId=authentication.user_id,
            name="my goal",
            howMuch=1,
            startInstant=self.start_time
        )
        good_goal_id = self.test_create_goal(good_goal, authentication)
        bad_goal = good_goal
        bad_goal.desireId -= 1
        # test
        self.test_update_goal(good_goal_id, bad_goal, authentication, 404)  # bad desireId
        bad_goal.desireId = desire_id
        bad_goal.howMuch = -1
        self.test_update_goal(good_goal_id, bad_goal, authentication, 400)  # bad howMuch
        bad_goal.howMuch = 1
        bad_goal.name = ""
        self.test_update_goal(good_goal_id, bad_goal, authentication, 400)  # bad name
        bad_goal.name = "goal"
        bad_goal.startInstant = None
        self.test_update_goal(good_goal_id, bad_goal, authentication, 400)  # bad startInstant
        bad_goal.startInstant = self.start_time
        bad_goal.endInstant = self.start_time - 1000000
        self.test_update_goal(good_goal_id, bad_goal, authentication, 400)  # bad endInstant
        # clean up
        self.test_delete_goal(good_goal_id, authentication)

    def test_get_with_malformed_params(self, authentication: Authentication, desire_id: int):
        self.test_get_goal(-1, authentication, 404)

    def test_call_functions_without_authentication(self, authentication: Authentication, another_authentication: Authentication, desire_id: int):
        good_goal = Goal(
            desireId=desire_id,
            userId=authentication.user_id,
            name="my goal",
            howMuch=1,
            startInstant=self.start_time
        )
        good_goal_id = self.test_create_goal(good_goal, authentication)
        # test
        self.test_create_goal(good_goal, another_authentication, 401)
        self.test_update_goal(good_goal_id, good_goal, another_authentication, 401)
        self.test_delete_goal(good_goal_id, another_authentication, 401)
        # cleanup
        self.test_delete_goal(good_goal_id, authentication)

    def test_create_goal(self, goal: Goal, authentication: Authentication, expected_response_code: int = 200):
        res = requests.post(self.goals_url, json=create_authenticated_request_body("goal", goal, authentication))
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            return res.json()["goal_id"]

    def test_get_goal(self, goal_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.goals_url + "/" + str(goal_id),
                           json=authentication.__dict__)
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            return res.json()["goal"]

    def test_get_goals(self, start_day: Optional[float], authentication: Authentication,
                            expected_response_code: int = 200):
        res = requests.get(self.get_goals_by_days_range, params={"start_day": start_day}, json=authentication.__dict__)
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            return res.json()["goals"]

    def test_update_goal(self, goal_id: int, updated_goal: Goal, authentication: Authentication,
                           expected_response_code: int = 200):
        res = requests.put(self.goals_url + "/" + str(goal_id),
                           json=create_authenticated_request_body("updated_goal", updated_goal, authentication))
        compare_responses(res, expected_response_code)

    def test_delete_goal(self, goal_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.delete(self.goals_url + "/" + str(goal_id), json=authentication.__dict__)
        compare_responses(res, expected_response_code)
