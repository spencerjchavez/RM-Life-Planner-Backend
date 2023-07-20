# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

import json
import requests
from UserEndpointsTest import UserEndpointsTest

sample_users: dict
base_url = "http://localhost:8000/api"
calendar_events_url = base_url + "/calendar/events"
todos_url = base_url + "/calendar/todos"
alerts_url = base_url + "/calendar/alerts"

test_user_endpoints = True
test_calendar_endpoints = True
test_goal_achieving_endpoints = True


if __name__ == '__main__':
    with open('../sample_objects/users.json', 'r') as file:
        ulist = json.load(file)
        sample_users = ulist

    # reset database
    print("resetting databases")
    res = requests.post("http://localhost:8000/api/testing/reset_tables")
    print("databases successfully reset")

    if test_user_endpoints:
        UserEndpointsTest(sample_users)
    if test_calendar_endpoints:

    if test_goal_achieving_endpoints:



    # testing Calendar stuff!!

    print("PASSED ALL TESTS!!!")