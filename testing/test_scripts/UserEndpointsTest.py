import requests
from TestingHelperFunctions import *
from testing.sample_objects.Users import *
from models.Authentication import Authentication
import json


class UserEndpointsTest:

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.users_url = base_url + "/users"
        self.register_url = self.users_url + "/register"
        self.login_url = self.users_url + "/login"
        self.logout_url = self.users_url + "/logout"

    def test_register_user(self, user: User, expected_response_code: int = 200):
        res = requests.post(self.register_url, json=user.__dict__)
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            auth_dict = res.json()["authentication"]
            return Authentication(user_id=auth_dict["user_id"], api_key=auth_dict["api_key"])

    def test_login_user(self, user: User, expected_response_code: int = 200):
        req_dict = {"username": user.username, "password": user.password}
        res = requests.post(self.login_url, params=req_dict)
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            auth_dict = res.json()["authentication"]
            return Authentication(user_id=auth_dict["user_id"], api_key=auth_dict["api_key"])

    def test_get_user(self, authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.users_url + "/" + str(authentication.user_id), json=authentication.__dict__)
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            return res.json()["user"]

    def test_update_user(self, updated_user: User, authentication: Authentication, expected_response_code: int = 200):
        res = requests.put(self.users_url + "/" + str(authentication.user_id),
                           json=create_authenticated_request_body("updated_user", updated_user, authentication))
        compare_responses(res, expected_response_code)

    def test_logout_user(self, authentication: Authentication, expected_response_code: int = 200):
        res = requests.post(self.logout_url + "/" + str(authentication.user_id), json=authentication.__dict__)
        compare_responses(res, expected_response_code)

    def test_delete_user(self, authentication: Authentication, expected_response_code: int = 200):
        res = requests.delete(self.users_url + "/" + str(authentication.user_id), json=authentication.__dict__)
        compare_responses(res, expected_response_code)

    def launch_user_test(self):
        # reset database
        print("resetting databases")
        res = requests.post("http://localhost:8000/api/testing/reset_tables")
        print("databases successfully reset")

        # test register endpoint
        USER1_AUTH = self.test_register_user(USER1)
        USER2_AUTH = self.test_register_user(USER2)
        self.test_register_user(INVALID_USER2_REPEAT, 400)
        USER3_AUTH = self.test_register_user(USER3)

        self.test_register_user(INVALID_USER1, 400)
        self.test_register_user(INVALID_USER2, 400)
        self.test_register_user(INVALID_USER3, 400)
        self.test_register_user(INVALID_USER4, 400)
        self.test_register_user(INVALID_USER5, 400)
        self.test_register_user(INVALID_USER6, 400)
        self.test_register_user(INVALID_USER7, 400)
        self.test_register_user(INVALID_USER8, 400)
        self.test_register_user(INVALID_USER9, 400)
        self.test_register_user(INVALID_USER10, 400)

        # test logout
        self.test_logout_user(USER2_AUTH)
        self.test_logout_user(USER3_AUTH)

        # test login
        USER1_AUTH = self.test_login_user(USER1)
        USER2_AUTH = self.test_login_user(USER2)
        USER3_AUTH = self.test_login_user(USER3)
        USER3_AUTH = self.test_login_user(USER3)

        # test get users
        self.test_get_user(USER1_AUTH)
        self.test_get_user(USER2_AUTH)
        self.test_get_user(USER3_AUTH)

        self.test_logout_user(USER1_AUTH)
        self.test_get_user(USER1_AUTH, 401)

        #test update users
        USER1_AUTH = self.test_login_user(USER1)
        USER1.email = "new_email@gmail.com"
        self.test_update_user(USER1, USER1_AUTH)
        if self.test_get_user(USER1_AUTH)["email"] != USER1.email:
            raise ValueError("User not updated properly")

        # test delete user
        self.test_delete_user(USER2_AUTH)
        self.test_delete_user(USER3_AUTH)
        self.test_login_user(USER2, 404)
        self.test_login_user(USER3, 404)

        print("PASSED USER ENDPOINT TEST!!")
