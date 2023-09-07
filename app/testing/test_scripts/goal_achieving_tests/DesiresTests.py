import requests
from app.models.Authentication import Authentication
from app.testing.test_scripts.UserEndpointsTest import UserEndpointsTest
from app.models.Desire import Desire
from app.testing.test_scripts.TestingHelperFunctions import *
from app.testing.sample_objects.Users import *


class DesiresTests:

    def __init__(self, base_url: str, user_tests: UserEndpointsTest):
        self.base_url = base_url
        self.desire_url = base_url + "/desires"
        self.user_tests = user_tests

    def launch_test(self):
        print("starting desires test")
        requests.post(self.base_url + "/testing/reset_tables")
        user1_auth = self.user_tests.test_register_user(USER1)
        user2_auth = self.user_tests.test_register_user(USER2)
        user3_auth = self.user_tests.test_register_user(USER3)

        self.test_happy_path(user1_auth)
        self.test_malformed_inputs(user1_auth, user2_auth)
        print("passed desire test!")

    def test_happy_path(self, authentication: Authentication):
        # setup
        desire = Desire(
            name="my desire",
            userId=authentication.user_id,
            dateCreated="2000-08-15",
            priorityLevel=1,
            colorR=0,
            colorG=0,
            colorB=0
        )
        updated_desire = desire.copy()
        updated_desire.name = "my updated desire"
        updated_desire.dateRetired = "2010-08-15"
        # test create, update, get, delete
        desire_id = self.test_create_desire(desire, authentication)
        self.test_update_desire(desire_id, updated_desire,authentication)
        desire_retrieved = self.test_get_desire(desire_id, authentication)
        assert desire_retrieved["name"] == updated_desire.name
        assert desire_retrieved["dateRetired"] == updated_desire.dateRetired
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
            dateCreated="2000-08-15",
            priorityLevel=1,
            colorR=0,
            colorG=0
        )
        self.test_create_desire(bad_desire, authentication, 400)  # missing colorB
        bad_desire.colorB = 0
        bad_desire.userId = -1
        self.test_create_desire(bad_desire, authentication, 401)  # missing correct userId
        bad_desire.userId = authentication.user_id
        bad_desire.name = None
        self.test_create_desire(bad_desire, authentication, 400)  # missing name

    def test_update_with_malformed_desires(self, authentication: Authentication):
        # setup
        good_desire = Desire(
            name="my desire",
            userId=authentication.user_id,
            dateCreated="2010-08-15",
            priorityLevel=1,
            colorR=0,
            colorG=0,
            colorB=0
        )
        good_desire_id = self.test_create_desire(good_desire, authentication)
        bad_desire = good_desire.copy()
        bad_desire.colorB = None
        # test
        self.test_update_desire(good_desire_id, bad_desire, authentication, 400)  # missing colorB
        bad_desire.colorB = 0
        bad_desire.userId = -1
        self.test_update_desire(good_desire_id, bad_desire, authentication, 401)  # missing good userId
        bad_desire.userId = authentication.user_id
        bad_desire.name = None
        self.test_update_desire(good_desire_id, bad_desire, authentication, 400)  # missing name

        # clean up
        self.test_delete_desire(good_desire_id, authentication)

    def test_get_with_malformed_params(self, authentication: Authentication):
        self.test_get_desire(10, authentication, 404)

    def test_call_functions_without_authentication(self, authentication: Authentication, another_authentication: Authentication):
        # setup
        desire = Desire(
            name="my desire",
            userId=authentication.user_id,
            dateCreated="2010-08-15",
            priorityLevel=1,
            colorR=0,
            colorG=0,
            colorB=0
        )
        updated_desire = desire.copy()
        updated_desire.name = "updated desire"
        updated_desire.userId = another_authentication.user_id
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
        if expected_response_code == 200:
            return res.json()["desire_id"]

    def test_get_desire(self, desire_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.desire_url + "/" + str(desire_id),
                           params={"auth_user": authentication.user_id, "api_key": authentication.api_key})
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            return res.json()["desire"]

    def test_update_desire(self, desire_id: int, updated_desire: Desire, authentication: Authentication,
                           expected_response_code: int = 200):
        res = requests.put(self.desire_url + "/" + str(desire_id),
                           json=create_authenticated_request_body("updated_desire", updated_desire, authentication))
        compare_responses(res, expected_response_code)

    def test_delete_desire(self, desire_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.delete(self.desire_url + "/" + str(desire_id), params={"auth_user": authentication.user_id, "api_key": authentication.api_key})
        compare_responses(res, expected_response_code)
