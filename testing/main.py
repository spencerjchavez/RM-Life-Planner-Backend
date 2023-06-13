# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

import json
from random import random
import requests
from requests import Response

def compare_responses(response_actual: Response, status_code_expected: int = 200, content_expected: str = None):
    if response_actual.status_code != status_code_expected:
        raise ValueError(
            f"server returned unexpected status code {response_actual.status_code}, ought to have returned {status_code_expected}")
    if response_actual.content != content_expected and content_expected is not None:
        raise ValueError(
            f"server returned unexpected content {response_actual.status_code}, ought to have returned {content_expected}")


def print_res(_response: Response):
    print(f"status code = {_response.status_code}; content = {_response.content}")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # Routes()
    base_url = "http://localhost:8000/api"
    users_url = base_url + "/users"
    register_url = users_url + "/register"
    login_url = users_url + "/login"
    logout_url = users_url + "/logout"
    calendar_events_url = "/calendars/events"
    with open('users.json', 'r') as file:
        ulist = json.load(file)
        sample_users = ulist

    # test register endpoint
    res = requests.post(register_url, data=json.dumps(sample_users["user1"]))
    compare_responses(res, 200)
    sample_users["user1"]["authentication"] = res.json()[0]
    res = requests.post(register_url, data=json.dumps(sample_users["user2"]))
    compare_responses(res, 200)
    sample_users["user2"]["authentication"] = res.json()[0]

    res = requests.post(register_url, data=json.dumps(sample_users["user2repeat"]))
    compare_responses(res, 400)

    res = requests.post(register_url, data=json.dumps(sample_users["user3"]))
    compare_responses(res, 200)
    sample_users["user3"]["authentication"] = res.json()[0]

    res = requests.post(register_url, data=json.dumps(sample_users["invalid1"]))
    compare_responses(res, 400)
    res = requests.post(register_url, data=json.dumps(sample_users["invalid2"]))
    compare_responses(res, 400)
    res = requests.post(register_url, data=json.dumps(sample_users["invalid3"]))
    compare_responses(res, 400)
    res = requests.post(register_url, data=json.dumps(sample_users["invalid4"]))
    compare_responses(res, 400)
    res = requests.post(register_url, data=json.dumps(sample_users["invalid5"]))
    compare_responses(res, 400)
    res = requests.post(register_url, data=json.dumps(sample_users["invalid6"]))
    compare_responses(res, 400)
    res = requests.post(register_url, data=json.dumps(sample_users["invalid7"]))
    compare_responses(res, 400)
    res = requests.post(register_url, data=json.dumps(sample_users["invalid8"]))
    compare_responses(res, 400)
    res = requests.post(register_url, data=json.dumps(sample_users["invalid9"]))
    compare_responses(res, 400)
    res = requests.post(register_url, data=json.dumps(sample_users["invalid10"]))
    compare_responses(res, 400)

    # test logout
    res = requests.post(logout_url, params=sample_users["user1"]["authentication"])
    compare_responses(res, 200)
    res = requests.post(logout_url, params=sample_users["user2"]["authentication"])
    compare_responses(res, 200)
    res = requests.post(logout_url, params=sample_users["user3"]["authentication"])
    compare_responses(res, 200)

    # test login
    user = sample_users["user1"]
    res = requests.post(login_url, params={"username": user['username'], "password": user['password']})
    sample_users["user1"]["authentication"] = res.json()[0]
    compare_responses(res, 200)
    user = sample_users["user2"]
    res = requests.post(login_url, params={"username": user['username'], "password": user['password']})
    sample_users["user2"]["authentication"] = res.json()[0]
    compare_responses(res, 200)
    user = sample_users["user3"]
    res = requests.post(login_url, params={"username": user['username'], "password": user['password']})
    sample_users["user3"]["authentication"] = res.json()[0]
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

    user = sample_users["user1"]
    res = requests.get(users_url, params=user["authentication"])
    print(res.json()[0])
    compare_responses(res, 200)
    user = sample_users["user2"]
    res = requests.get(users_url, params=user["authentication"])
    compare_responses(res, 200)
    user = sample_users["user3"]
    res = requests.get(users_url, params=user["authentication"])
    compare_responses(res, 200)

    # test delete user
    user = sample_users["user1"]
    res = requests.delete(users_url, params=user["authentication"])
    compare_responses(res, 200)
    res = requests.delete(users_url, params=user["authentication"])
    compare_responses(res, 401)
    res = requests.post(login_url, params={"username": user['username'], "password": user['password']})
    compare_responses(res, 400)
    del user["authentication"] # need to clear authentication or fastapi will get mad in passing the object to the register_user endpoint
    res = requests.post(register_url, data=json.dumps(user))
    compare_responses(res, 200)
    sample_users["user1"]["authentication"] = res.json()[0]

    # testing Calendar stuff!!





    print("PASSED ALL TESTS!!!")

