from typing import Optional

import requests
from app.models.Goal import Goal
from app.models.Authentication import Authentication
from app.testing.test_scripts.goal_achieving_tests.DesiresTests import DesiresTests
from app.testing.test_scripts.UserEndpointsTest import UserEndpointsTest
from app.models.Desire import Desire


class GoalsTests:

    def __init__(self, base_url: str, user_tests: UserEndpointsTest, desire_tests: DesiresTests):
        self.base_url = base_url
        self.goals_url = base_url + "/goals"
        self.get_goals_by_id_url = self.goals_url + "/by-goal-id"
        self.get_goals_by_days_list = self.goals_url + "/in-date-list"
        self.get_goals_by_days_range = self.goals_url + "/in-date-range"
        self.user_tests = user_tests
        self.desire_tests = desire_tests
        self.start_time = "1999-07-04"
        self.start_time2 = "1999-08-05"
        self.bad_date = "1999-77-04"

    def launch_test(self):
        print("starting goals test")
        requests.post(self.base_url + "/testing/reset_tables")
        user1_auth = self.user_tests.test_register_user(USER1)
        user2_auth = self.user_tests.test_register_user(USER2)

        # setup sample desire, goal, and event for plans to be tested with
        desire = Desire(
            name="my desire",
            userId=user1_auth.user_id,
            dateCreated="1991-01-01",
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
        print("passed goals test!")

    def test_happy_path(self, authentication: Authentication, desire_id: int):
        goal = Goal(
            desireId=desire_id,
            userId=authentication.user_id,
            name="my goal",
            howMuch=1,
            startDate=self.start_time
        )
        updated_goal = goal.copy()
        updated_goal.name = "updated goal"
        # test create, update, get, and delete
        goal_id = self.test_create_goal(goal, authentication)
        self.test_update_goal(goal_id, updated_goal, authentication)
        goal_retrieved = self.test_get_goal(goal_id, authentication)
        assert goal_retrieved["name"] == updated_goal.name
        # test get goals by day
        goals_retrieved = self.test_get_goals(self.start_time, authentication)
        assert len(goals_retrieved) == 1
        assert goals_retrieved[0]["name"] == updated_goal.name
        goals_retrieved = self.test_get_goals(self.start_time2, authentication)
        assert len(goals_retrieved) == 1
        # updated startInstant and check again
        updated_goal.startDate = self.start_time2
        self.test_update_goal(goal_id, updated_goal, authentication)
        goals = self.test_get_goals(self.start_time, authentication)
        assert len(goals) == 0
        goals = self.test_get_goals(self.start_time2, authentication)
        assert len(goals) == 1
        self.test_delete_goal(goal_id, authentication)
        # assert that delete worked
        goals_retrieved = self.test_get_goals(self.start_time2, authentication)
        assert len(goals_retrieved) == 0

    def test_malformed_inputs(self, authentication: Authentication, another_authentication: Authentication,
                              desire_id: int):
        self.test_create_malformed_goals(authentication, desire_id)
        self.test_update_with_malformed_goals(authentication, desire_id)
        self.test_get_with_malformed_params(authentication, desire_id)
        self.test_call_functions_without_authentication(authentication, another_authentication, desire_id)

    def test_create_malformed_goals(self, authentication: Authentication, desire_id: int):
        bad_goal = Goal(
            desireId=desire_id - 1,
            userId=authentication.user_id,
            name="my goal",
            howMuch=1,
            startDate=self.start_time
        )
        self.test_create_goal(bad_goal, authentication, 404)  # bad desireId
        bad_goal.desireId = desire_id
        bad_goal.howMuch = -1
        self.test_create_goal(bad_goal, authentication, 400)  # bad howMuch
        bad_goal.howMuch = 1
        bad_goal.name = ""
        self.test_create_goal(bad_goal, authentication, 400)  # bad goal name
        bad_goal.name = "goal"
        bad_goal.startDate = None
        self.test_create_goal(bad_goal, authentication, 400)  # bad startDate
        bad_goal.startDate = self.bad_date
        self.test_create_goal(bad_goal, authentication, 400)  # bad startDate
        bad_goal.startDate = self.start_time2
        bad_goal.deadlineDate = self.start_time
        self.test_create_goal(bad_goal, authentication, 400)  # bad deadlineDate

    def test_update_with_malformed_goals(self, authentication: Authentication, desire_id: int):
        # setup
        good_goal = Goal(
            desireId=desire_id,
            userId=authentication.user_id,
            name="my goal",
            howMuch=1,
            startDate=self.start_time
        )
        good_goal_id = self.test_create_goal(good_goal, authentication)
        bad_goal = good_goal.copy()
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
        bad_goal.startDate = None
        self.test_update_goal(good_goal_id, bad_goal, authentication, 400)  # bad startInstant
        bad_goal.startDate = self.bad_date
        self.test_update_goal(good_goal_id, bad_goal, authentication, 400)  # bad startInstant
        bad_goal.startDate = self.start_time2
        bad_goal.deadlineDate = self.start_time
        self.test_update_goal(good_goal_id, bad_goal, authentication, 400)  # bad endInstant
        # clean up
        self.test_delete_goal(good_goal_id, authentication)

    def test_get_with_malformed_params(self, authentication: Authentication, desire_id: int):
        self.test_get_goal(-1, authentication, 404)
        self.test_get_goals(self.bad_date, authentication, 400)

    def test_call_functions_without_authentication(self, authentication: Authentication,
                                                   another_authentication: Authentication, desire_id: int):
        good_goal = Goal(
            desireId=desire_id,
            userId=authentication.user_id,
            name="my goal",
            howMuch=1,
            startDate=self.start_time
        )
        good_goal_id = self.test_create_goal(good_goal, authentication)
        # test
        self.test_create_goal(good_goal, another_authentication, 401)
        self.test_update_goal(good_goal_id, good_goal, another_authentication, 401)
        self.test_get_goal(good_goal_id, another_authentication, 401)
        self.test_delete_goal(good_goal_id, another_authentication, 401)
        good_goal.userId = another_authentication.user_id
        self.test_update_goal(good_goal_id, good_goal, another_authentication, 401)
        # cleanup
        self.test_delete_goal(good_goal_id, authentication)

    def test_create_goal(self, goal: Goal, authentication: Authentication, expected_response_code: int = 200):
        res = requests.post(self.goals_url, json=create_authenticated_request_body("goal", goal, authentication))
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            return res.json()["goal_id"]

    def test_get_goal(self, goal_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.get_goals_by_id_url + "/" + str(goal_id),
                           json=authentication.__dict__)
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            return res.json()["goal"]

    def test_get_goals(self, start_date: Optional[str], authentication: Authentication,
                       expected_response_code: int = 200):
        res = requests.get(self.get_goals_by_days_range, params={"start_date": start_date},
                           json=authentication.__dict__)
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
