import time

import requests
from testing.test_scripts.TestingHelperFunctions import *
from models.Plan import Plan
from models.Authentication import Authentication
from testing.sample_objects.Users import *
from testing.test_scripts.UserEndpointsTest import UserEndpointsTest
from testing.test_scripts.goal_achieving_tests.GoalsTests import GoalsTests, Goal
from testing.test_scripts.goal_achieving_tests.DesiresTests import DesiresTests, Desire
from testing.test_scripts.calendar_item_tests.CalendarEventTests import CalendarEventTests, CalendarEvent


class PlansTests:

    def __init__(self, base_url: str, user_tests: UserEndpointsTest, desire_tests: DesiresTests, goal_tests: GoalsTests, event_tests: CalendarEventTests):
        self.base_url = base_url
        self.plans_url = base_url + "/plans"
        self.user_tests = user_tests
        self.desire_tests = desire_tests
        self.goal_tests = goal_tests
        self.event_tests = event_tests

    def launch_test(self):
        print("starting event tests")
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
        goal = Goal(
            desireId=desire_id,
            userId=user1_auth.user_id,
            name="my goal",
            howMuch=1,
            startInstant=time.time()
        )
        goal_id = self.goal_tests.test_create_goal(goal, user1_auth)
        event = CalendarEvent(
            name="event",
            description="this is the description i have written, it is rather long, but not too long. hopefully it doesn't take too long to insert all these letters into the database!!! I'm sure it won't be a problem though. All is well in the world.",
            startInstant=time.time(),
            endInstant=time.time() + 10000,
            userId=user1_auth.user_id
        )
        event_id = self.event_tests.test_create_event(event, user1_auth)
        self.test_happy_path(user1_auth, goal_id, event_id)
        self.test_malformed_inputs(user1_auth, user2_auth, goal_id, event_id)

    def test_happy_path(self, authentication: Authentication, goal_id: int, event_id: int):
        # setup
        plan = Plan(
            userId=authentication.user_id,
            goalId=goal_id,
            eventId=event_id,
            howMuch=1,
            howMuchAccomplished=0
        )
        updated_plan = plan
        updated_plan.howMuchAccomplished = 1
        # test create, updated, get, and delete
        plan_id = self.test_create_plan(plan, authentication)
        self.test_update_plan(plan_id, updated_plan, authentication)
        self.test_delete_plan(plan_id, authentication)
        # assert that delete worked
        self.test_get_plan(plan_id, authentication, 404)

    def test_malformed_inputs(self, authentication: Authentication, another_authentication: Authentication, goal_id: int, event_id: int):
        self.test_create_malformed_plans(authentication, goal_id, event_id)
        self.test_update_with_malformed_plans(authentication, goal_id, event_id)
        self.test_get_with_malformed_params(authentication, goal_id, event_id)
        self.test_call_functions_without_authentication(authentication, another_authentication, goal_id, event_id)

    def test_create_malformed_plans(self, authentication: Authentication, goal_id: int, event_id: int):
        # setup
        bad_plan = Plan(
            goalId=goal_id,
            eventId=event_id,
            howMuch=1,
            howMuchAccomplished=0
        )
        # test
        self.test_create_plan(bad_plan, authentication, 400)  # plan is missing userId
        bad_plan.userId = authentication.user_id
        bad_plan.goalId = -1
        self.test_create_plan(bad_plan, authentication, 404)  # plan has bad goalid
        bad_plan.goalId = goal_id
        bad_plan.eventId = -1
        self.test_create_plan(bad_plan, authentication, 404)  # plan has bad eventId
        bad_plan.eventId = event_id
        bad_plan.howMuch = 0
        self.test_create_plan(bad_plan, authentication, 400)  # plan has bad howMuch

    def test_update_with_malformed_plans(self, authentication: Authentication, goal_id: int, event_id: int):
        # setup
        good_plan = Plan(
            userId=authentication.user_id,
            goalId=goal_id,
            eventId=event_id,
            howMuch=1,
            howMuchAccomplished=0
        )
        good_plan_id = self.test_create_plan(good_plan, authentication)
        bad_plan = good_plan
        bad_plan.userId = -1
        # test update
        self.test_update_plan(good_plan_id, bad_plan, authentication, 400)  # plan is missing userId
        bad_plan.userId = authentication.user_id
        bad_plan.goalId = -1
        self.test_update_plan(good_plan_id, bad_plan, authentication, 404)  # plan has bad goalid
        bad_plan.goalId = goal_id
        bad_plan.eventId = -1
        self.test_update_plan(good_plan_id, bad_plan, authentication, 404)  # plan has bad eventId
        bad_plan.eventId = event_id
        bad_plan.howMuch = 0
        self.test_update_plan(good_plan_id, bad_plan, authentication, 400) # plan has bad howMuch
        # cleanup
        self.test_delete_plan(good_plan_id, authentication)

    def test_get_with_malformed_params(self, authentication: Authentication, goal_id: int, event_id: int):
        self.test_get_plan(10, authentication, 404)

    def test_call_functions_without_authentication(self, authentication: Authentication, another_authentication: Authentication, goal_id: int, event_id: int):
        # setup
        plan = Plan(
            userId=authentication.user_id,
            goalId=goal_id,
            eventId=event_id,
            howMuch=1
        )
        updated_plan = plan
        updated_plan.howMuchAccomplished = 1
        plan_id = self.test_create_plan(plan, authentication)
        # test
        self.test_create_plan(plan, another_authentication, 401)
        self.test_update_plan(plan_id, updated_plan, another_authentication, 401)
        self.test_delete_plan(plan_id, another_authentication, 401)

    def test_create_plan(self, plan: Plan, authentication: Authentication, expected_response_code: int = 200):
        res = requests.post(self.plans_url, json=create_authenticated_request_body("plan", plan, authentication))
        compare_responses(res, expected_response_code)
        return res.json()["plan_id"]

    def test_get_plan(self, plan_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.plans_url + "/" + str(plan_id),
                           json=authentication.json())
        compare_responses(res, expected_response_code)
        return res

    def test_update_plan(self, plan_id: int, updated_plan: Plan, authentication: Authentication,
                           expected_response_code: int = 200):
        res = requests.put(self.plans_url + "/" + str(plan_id),
                           json=create_authenticated_request_body("updated_plan", updated_plan, authentication))
        compare_responses(res, expected_response_code)

    def test_delete_plan(self, plan_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.delete(self.plans_url + "/" + str(plan_id), json=authentication.json())
        compare_responses(res, expected_response_code)
