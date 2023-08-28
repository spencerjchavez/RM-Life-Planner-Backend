import requests

from models.Desire import Desire
from models.Goal import Goal
from testing.test_scripts.TestingHelperFunctions import *
from ..UserEndpointsTest import UserEndpointsTest
from testing.sample_objects.Users import *
from models.ToDo import ToDo
from ..goal_achieving_tests.DesiresTests import DesiresTests
from ..goal_achieving_tests.GoalsTests import GoalsTests


class ToDoTests:

    def __init__(self, base_url: str, desire_tests: DesiresTests, goal_tests: GoalsTests):
        self.todo_url = base_url + "/calendar/todos"
        self.get_todos_by_todo_id = self.todo_url + "/by-todo-id"
        self.get_todos_by_days_list_url = self.todo_url + "/in-date-list"
        self.get_todos_by_days_range_url = self.todo_url + "/in-date-range"
        self.base_url = base_url
        self.user_tests = UserEndpointsTest(base_url)
        self.desire_tests = desire_tests
        self.goal_tests = goal_tests
        self.start_date1 = "1999-07-04"
        self.start_date2 = "2000-12-24"
        self.bad_date = "999-77-04"

    def launch_test(self):
        print("starting todo tests")
        requests.post(self.base_url + "/testing/reset_tables")

        user1_auth = self.user_tests.test_register_user(USER1)
        user2_auth = self.user_tests.test_register_user(USER2)
        desire = Desire(
            name="my desire",
            userId=user1_auth.user_id,
            dateCreated="2010-08-15",
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
            startDate=self.start_date1
        )
        goal_id = self.goal_tests.test_create_goal(goal, user1_auth)
        self.test_happy_path(user1_auth, goal_id)
        self.test_malformed_inputs(user1_auth, user2_auth, goal_id)
        print("passed todo test!")

    def test_malformed_inputs(self, authentication: Authentication, another_authentication: Authentication, goal_id: int):
        self.test_create_malformed_todos(authentication, goal_id)
        self.test_get_with_malformed_params(authentication)
        self.test_update_with_malformed_todos(authentication, goal_id)
        self.test_call_functions_without_authentication(authentication, another_authentication)

    def test_create_malformed_todos(self, authentication: Authentication, goal_id: int):
        bad_todo = ToDo()
        self.test_create_todo(bad_todo, authentication, 400)
        bad_todo.userId = authentication.user_id
        self.test_create_todo(bad_todo, authentication, 400)
        bad_todo.name = "todo"
        bad_todo.deadlineDate = self.start_date1
        self.test_create_todo(bad_todo, authentication, 400)
        bad_todo.startDate = self.start_date1
        bad_todo.linkedGoalId = -1
        bad_todo.howMuchPlanned = 1
        self.test_create_todo(bad_todo, authentication, 404)
        bad_todo.linkedGoalId = None
        bad_todo.startDate = self.start_date2  # start instant after endInstant
        self.test_create_todo(bad_todo, authentication, 400)
        bad_todo.startDate = self.start_date1
        bad_todo.linkedGoalId = goal_id
        bad_todo.howMuchPlanned = 0
        self.test_create_todo(bad_todo, authentication, 400)

    def test_get_with_malformed_params(self, authentication: Authentication):
        self.test_get_todos_by_day_range(self.bad_date, authentication, 400)
        self.test_get_todo(-1, authentication, 404)

    def test_update_with_malformed_todos(self, authentication: Authentication, goal_id: int):
        # setup
        good_todo = ToDo(
            name="go to the store today",
            startDate=self.start_date1,
            deadlineDate=self.start_date1,
            userId=authentication.user_id,
            linkedGoalId=goal_id,
            howMuchPlanned=1
        )
        good_todo_id = self.test_create_todo(good_todo, authentication)
        # test
        bad_todo = good_todo.copy()
        bad_todo.userId = -1
        self.test_update_todo(good_todo_id, bad_todo, authentication, 401)
        bad_todo.userId = authentication.user_id
        bad_todo.startDate = self.start_date2
        bad_todo.deadlineDate = self.start_date1
        self.test_update_todo(good_todo_id, bad_todo, authentication, 400)
        bad_todo.startDate = self.start_date1
        bad_todo.howMuchPlanned = None
        self.test_update_todo(good_todo_id, bad_todo, authentication, 400)
        bad_todo.linkedGoalId = -1
        bad_todo.howMuchPlanned = 1
        self.test_update_todo(good_todo_id, bad_todo, authentication, 404)

        # cleanup
        self.test_delete_todo(good_todo_id, authentication)

    def test_call_functions_without_authentication(self, real_authentication: Authentication,
                                                   another_real_authentication: Authentication):
        # setup
        real_todo = ToDo(
            name="go to the store today",
            startDate=self.start_date1,
            userId=real_authentication.user_id,
            howMuchPlanned=1
        )
        real_todo_id = self.test_create_todo(real_todo, real_authentication)
        updated_real_todo = real_todo.copy()
        updated_real_todo.name = "updated todo"
        # test
        self.test_create_todo(real_todo, another_real_authentication, 401)
        self.test_update_todo(real_todo_id, updated_real_todo, another_real_authentication, 401)
        self.test_delete_todo(real_todo_id, another_real_authentication, 401)
        updated_real_todo.userId = another_real_authentication.user_id
        self.test_update_todo(real_todo_id, updated_real_todo, another_real_authentication, 401)

        # cleanup
        self.test_delete_todo(real_todo_id, real_authentication)

    def test_happy_path(self, authentication: Authentication, goal_id: int):
        #setup
        todo = ToDo(
            name="todo",

            userId=authentication.user_id,
            startDate=self.start_date1,
            deadlineDate=self.start_date1,
            linkedGoalId=goal_id,
            howMuchPlanned=1
        )
        updated_todo = todo.copy()
        updated_todo.name = "updated todo"
        # test create, get, update and delete happy path todos
        # get todos by day, should return nothing
        events = self.test_get_todos_by_day(self.start_date1, authentication)
        assert len(events) == 0

        # create
        todo.todoId = self.test_create_todo(todo, authentication)
        self.test_update_todo(todo.todoId, updated_todo, authentication)

        todo_received = self.test_get_todo(todo.todoId, authentication)
        assert updated_todo.name == todo_received["name"]

        todos_received = self.test_get_todos_by_day(self.start_date1, authentication)
        assert len(todos_received) == 1
        assert updated_todo.name == todos_received[0]["name"]
        # delete todos
        self.test_delete_todo(todo.todoId, authentication)
        # assert that delete functioned correctly
        self.test_get_todo(todo.todoId, authentication, 404)

    def test_create_todo(self, todo: ToDo, authentication: Authentication,
                         expected_response_code: int = 200):
        if todo.userId is None:
            todo.userId = authentication.user_id
        res = requests.post(self.todo_url, json=create_authenticated_request_body("todo", todo, authentication))
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            return res.json()["todo_id"]

    def test_get_todo(self, todo_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.get_todos_by_todo_id + "/" + str(todo_id),
                           json=authentication.__dict__)
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            return res.json()["todo"]

    def test_get_todos_by_day(self, start_day: str, authentication: Authentication,
                              expected_response_code: int = 200):
        res = requests.get(self.get_todos_by_days_range_url, params={"start_date": start_day},
                           json=authentication.__dict__)
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            return res.json()["todos"]

    def test_get_todos_by_day_range(self, start_day: str, authentication: Authentication,
                                    expected_response_code: int = 200):
        res = requests.get(self.get_todos_by_days_range_url, params={"start_date": start_day, "end_date": start_day},
                           json=authentication.__dict__)
        compare_responses(res, expected_response_code)
        if expected_response_code == 200:
            return res.json()["todos"]

    def test_update_todo(self, todo_id: int, updated_todo: ToDo, authentication: Authentication,
                         expected_response_code: int = 200):
        if updated_todo.userId is None:
            updated_todo.userId = authentication.user_id
        res = requests.put(self.todo_url + "/" + str(todo_id),
                           json=create_authenticated_request_body("updated_todo", updated_todo, authentication))
        compare_responses(res, expected_response_code)

    def test_delete_todo(self, todo_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.delete(self.todo_url + "/" + str(todo_id), json=authentication.__dict__)
        compare_responses(res, expected_response_code)
