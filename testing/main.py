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
    calendar_events_url = "/calendars/events"
    with open('users.json', 'r') as file:
        ulist = json.load(file)
        sample_users = ulist
    # test get users where they don't exist
    for i in range(5):
        res = requests.get(users_url, {"user_id": int(random() * 100000), "api_key": "abcdefg"})
        compare_responses(res, 401)

    res = requests.get(users_url, {"user_id": 0, "api_key": None})
    compare_responses(res, 422)
    res = requests.get(users_url, {"user_id": None, "api_key": None})
    compare_responses(res, 422)
    res = requests.get(users_url, {"user_id": "", "api_key": ""})
    compare_responses(res, 422)

    res = requests.post(register_url, headers={"Content-Type": "application/json"}, data=json.dumps(sample_users["user1"]))
    compare_responses(res, 200)

