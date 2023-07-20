import requests
from requests import Response
from helper_functions import *


class UserEndpointsTest:

    def __init__(self, base_url: str, sample_objects_path: str):

        self.base_url = base_url
        self.sample_users = sample_users
        self.users_url = base_url + "/users"
        self.register_url = self.users_url + "/register"
        self.login_url = self.users_url + "/login"
        self.logout_url = self.users_url + "/logout"

    def test_register_user(self, username: str, expected_response_code: int = 200):
        res = requests.post(self.register_url, json=self.sample_users[username])
        compare_responses(res, expected_response_code)


    def test_login_user(self, username: str, expected_response_code: int = 200):
        res = requests.post(self.login_url, json=self.sample_users[username])
        compare_responses(res, expected_response_code)
        self.sample_users[username].update(res.json())


    def test_get_user(self, username: str, expected_response_code: int = 200):
        res = requests.get(self.users_url + "/" + user_id_of_user_as_str("user1"), json=self.sample_users[username])
        compare_responses(res, expected_response_code)


    def test_logout_user(self, username: str, expected_response_code: int = 200):
        res = requests.post(self.logout_url, json=self.sample_users[username])
        compare_responses(res, expected_response_code)


    def launch_user_test(self):
        # test register endpoint
        self.test_register_user("user1")
        self.test_register_user("user2")
        self.test_register_user("user2repeat")
        self.test_register_user("user3")

        self.test_register_user("invalid1", 400)
        self.test_register_user("invalid2", 400)
        self.test_register_user("invalid3", 400)
        self.test_register_user("invalid4", 400)
        self.test_register_user("invalid5", 400)
        self.test_register_user("invalid6", 400)
        self.test_register_user("invalid7", 400)
        self.test_register_user("invalid8", 400)
        self.test_register_user("invalid9", 400)
        self.test_register_user("invalid10", 400)

        # test logout

        res = requests.post(logout_url + "/" + str(user_id_of_user("user2")), json=self.sample_users["user2"]["authentication"])
        compare_responses(res, 200)
        res = requests.post(logout_url + "/" + str(user_id_of_user("user3")), json=self.sample_users["user3"]["authentication"])
        compare_responses(res, 200)

        # test login
        user = self.sample_users["user1"]
        res = requests.post(login_url, json={"username": user['username'], "password": user['password']})
        self.sample_users["user1"]["authentication"] = res.json()[0]
        compare_responses(res, 200)
        user = self.sample_users["user2"]
        res = requests.post(login_url, json={"username": user['username'], "password": user['password']})
        self.sample_users["user2"]["authentication"] = res.json()[0]
        compare_responses(res, 200)
        user = self.sample_users["user3"]
        res = requests.post(login_url, json={"username": user['username'], "password": user['password']})
        self.sample_users["user3"]["authentication"] = res.json()[0]
        compare_responses(res, 200)

        # test get users
        for i in range(5):
            res = requests.get(users_url, params={"user_id": int(random() * 100000), "api_key": "abcdefg"})
            compare_responses(res, 401)
        res = requests.get(users_url, params={"user_id": 0, "api_key": None})
        compare_responses(res, 422)
        res = requests.get(users_url, params={"user_id": None, "api_key": None})
        compare_responses(res, 422)
        res = requests.get(users_url, params={"user_id": "", "api_key": ""})
        compare_responses(res, 422)

        user = self.sample_users["user1"]
        res = requests.get(users_url, params=user["authentication"])
        print(res.json()[0])
        compare_responses(res, 200)
        user = self.sample_users["user2"]
        res = requests.get(users_url, params=user["authentication"])
        compare_responses(res, 200)
        user = self.sample_users["user3"]
        res = requests.get(users_url, params=user["authentication"])
        compare_responses(res, 200)

        # test delete user
        user = self.sample_users["user1"]
        res = requests.delete(users_url, params=user["authentication"])
        compare_responses(res, 200)
        res = requests.delete(users_url, params=user["authentication"])
        compare_responses(res, 401)
        res = requests.post(login_url, params={"username": user['username'], "password": user['password']})
        compare_responses(res, 400)
        del user[
            "authentication"]  # need to clear authentication or fastapi will get mad in passing the object to the register_user endpoint
        res = requests.post(register_url, json=user)
        compare_responses(res, 200)
        self.sample_users["user1"]["authentication"] = res.json()[0]