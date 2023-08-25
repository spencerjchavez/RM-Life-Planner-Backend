# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

from UserEndpointsTest import UserEndpointsTest
from testing.test_scripts.goal_achieving_tests.GoalAchievingTest import GoalAchievingEndpointsTest
from testing.test_scripts.calendar_item_tests.CalendarEndpointsTest import CalendarEndpointsTest

sample_users: dict
base_url = "http://localhost:8000/api"
calendar_events_url = base_url + "/calendar/events"
todos_url = base_url + "/calendar/todos"
alerts_url = base_url + "/calendar/alerts"

sample_users_path = '../sample_objects/users.py'

sample_events_path = '../sample_objects/calendar_items/events.py'
sample_todos_path = '../sample_objects/calendar_items/todos.py'
sample_recurrences_path = '../sample_objects/calendar_items/recurrences.py'
sample_alerts_path = '../sample_objects/calendar_items/alerts.py'

sample_desires_path = '../sample_objects/goal_achieving/desires.py'
sample_goals_path = '../sample_objects/goal_achieving/goals.py'
sample_plans_path = '../sample_objects/goal_achieving/plans.py'
sample_actions_path = '../sample_objects/goal_achieving/actions.py'


test_user_endpoints = False
test_calendar_endpoints = True
test_goal_achieving_endpoints = True


if __name__ == '__main__':
    if test_user_endpoints:
        UserEndpointsTest(base_url).launch_user_test()
    if test_calendar_endpoints:
        CalendarEndpointsTest(base_url).launch_test()
    if test_goal_achieving_endpoints:
        GoalAchievingEndpointsTest(base_url).launch_test()

    print("PASSED ALL TESTS!!!")
