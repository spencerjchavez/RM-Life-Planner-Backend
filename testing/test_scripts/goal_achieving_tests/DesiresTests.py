import requests
from testing.test_scripts.TestingHelperFunctions import *
from models.Authentication import Authentication
from testing.test_scripts.UserEndpointsTest import UserEndpointsTest
from testing.sample_objects.goal_achieving.desires import *
from testing.sample_objects.Users import *

class DesiresTests:

    def __init__(self, base_url: str, user_tests: UserEndpointsTest):
        self.base_url = base_url
        self.desire_url = base_url + "/desires"
        self.user_tests = user_tests

    def launch_test(self):
        print("starting event tests")
        print("resetting the database")
        requests.post(self.base_url + "/testing/reset_tables")
        print("databases successfully reset")
        user1_auth = self.user_tests.test_register_user(USER1)
        user2_auth = self.user_tests.test_register_user(USER2)
        user3_auth = self.user_tests.test_register_user(USER3)

        self.test_happy_path(user1_auth)
        self.test_malformed_inputs(user1_auth, user2_auth)

    def test_happy_path(self, authentication: Authentication):
        # setup
        desire = Desire(
            name="my desire",
            userId=authentication.user_id,
            dateCreated=time.time(),
            priorityLevel=1,
            colorR=0,
            colorG=0,
            colorB=0
        )
        updated_desire = desire
        updated_desire.name = "my updated desire"
        updated_desire.dateRetired = time.time() + 10000
        # test create, update, get, delete
        desire_id = self.test_create_desire(desire, authentication)
        self.test_update_desire(desire_id, updated_desire,authentication)
        desire_retrieved = self.test_get_desire(desire_id, authentication)
        assert(desire_retrieved["name"] == updated_desire.name)
        assert(desire_retrieved["date_retired"] == updated_desire.dateRetired)
        self.test_delete_desire(desire_id, authentication)
        # assert that delete worked
        self.test_get_desire(desire_id, authentication, 404)

    def test_malformed_inputs(self, authentication: Authentication, another_authentication: Authentication):
        self.test_create_malformed_desires(authentication)
        self.test_update_with_malformed_desires(authentication)
        self.test_get_with_malformed_params(authentication)
        self.test_call_functions_without_authentication(authentication, another_authentication)

    def test_create_malformed_desires(self, authentication: Authentication):
        bad_desire = Desire(
            name="my desire",
            userId=authentication.user_id,
            dateCreated=time.time(),
            priorityLevel=1,
            colorR=0,
            colorG=0
        )
        self.test_create_desire(bad_desire, authentication, 400)  # missing colorB
        bad_desire.colorB = 0
        bad_desire.userId = -1
        self.test_create_desire(bad_desire, authentication, 400)  # missing correct userId
        bad_desire.userId = authentication.user_id
        bad_desire.name = None
        self.test_create_desire(bad_desire, authentication, 400)  # missing name
        bad_desire.name = "desire"
        bad_desire.dateCreated = None
        self.test_create_desire(bad_desire, authentication, 400)  # missing dateCreated

    def test_update_with_malformed_desires(self, authentication: Authentication):
        # setup
        good_desire = Desire(
            name="my desire",
            userId=authentication.user_id,
            dateCreated=time.time(),
            priorityLevel=1,
            colorR=0,
            colorG=0,
            colorB=0
        )
        good_desire_id = self.test_create_desire(good_desire, authentication)
        bad_desire = good_desire
        bad_desire.colorB = None
        # test
        self.test_update_desire(good_desire_id, bad_desire, authentication, 400)  # missing colorB
        bad_desire.colorB = 0
        bad_desire.userId = -1
        self.test_update_desire(good_desire_id, bad_desire, authentication, 400)  # missing colorB
        bad_desire.userId = authentication.user_id
        bad_desire.name = None
        self.test_update_desire(good_desire_id, bad_desire, authentication, 400)  # missing colorB
        bad_desire.name = "desire"
        bad_desire.dateCreated = None
        self.test_update_desire(good_desire_id, bad_desire, authentication, 400)  # missing colorB

        # clean up
        self.test_delete_desire(good_desire_id, authentication)

    def test_get_with_malformed_params(self, authentication: Authentication):
        self.test_get_desire(10, authentication, 400)

    def test_call_functions_without_authentication(self, authentication: Authentication, another_authentication: Authentication):
        # setup
        desire = Desire(
            name="my desire",
            userId=authentication.user_id,
            dateCreated=time.time(),
            priorityLevel=1,
            colorR=0,
            colorG=0,
            colorB=0
        )
        updated_desire = desire
        updated_desire.name = "updated desire"
        desire_id = self.test_create_desire(desire, authentication)
        # test with improper authentication
        self.test_create_desire(desire, another_authentication, 401)
        self.test_update_desire(desire_id, updated_desire, another_authentication, 401)
        self.test_delete_desire(desire_id, another_authentication, 401)
        # cleanup
        self.test_delete_desire(desire_id, authentication)

    def test_create_desire(self, desire: Desire, authentication: Authentication, expected_response_code: int = 200):
        res = requests.post(self.desire_url, json=create_authenticated_request_body("desire", desire, authentication))
        compare_responses(res, expected_response_code)
        return res.json()["desire_id"]

    def test_get_desire(self, desire_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.desire_url + "/" + str(desire_id),
                           json=authentication.json())
        compare_responses(res, expected_response_code)
        return res.json()

    def test_update_desire(self, desire_id: int, updated_desire: Desire, authentication: Authentication,
                           expected_response_code: int = 200):
        res = requests.put(self.desire_url + "/" + str(desire_id),
                           json=create_authenticated_request_body("updated_desire", updated_desire, authentication))
        compare_responses(res, expected_response_code)

    def test_delete_desire(self, desire_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.delete(self.desire_url + "/" + str(desire_id), json=authentication.json())
        compare_responses(res, expected_response_code)
