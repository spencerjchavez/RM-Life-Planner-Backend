from dateutil import relativedelta
import requests
from testing.test_scripts.TestingHelperFunctions import *
from ..UserEndpointsTest import UserEndpointsTest
from testing.sample_objects.Users import *
from testing.sample_objects.calendar_items.todos import *


class ToDoTests:

    def __init__(self, base_url: str):
        self.todo_url = base_url + "/todos"
        self.get_todos_by_days_list_url = self.todo_url + "/by-days-list"
        self.get_todos_by_days_range_url = self.todo_url + "/by-days-range"
        self.base_url = base_url
        self.user_tests = UserEndpointsTest(base_url)

    def launch_test(self):
        print("starting todo tests")
        print("resetting the database")
        requests.post(self.base_url + "/testing/reset_tables")
        print("databases successfully reset")

        user1_auth = self.user_tests.test_register_user(USER1)
        user2_auth = self.user_tests.test_register_user(USER2)
        user3_auth = self.user_tests.test_register_user(USER3)

        self.test_happy_path(user1_auth)
        self.test_malformed_inputs(user1_auth, user2_auth)

    def test_malformed_inputs(self, authentication: Authentication, another_authentication: Authentication):
        self.test_create_malformed_todos(authentication)
        self.test_get_with_malformed_params(authentication)
        self.test_update_with_malformed_todos(authentication)
        self.test_call_functions_without_authentication(authentication, another_authentication)

    def test_create_malformed_todos(self, authentication: Authentication):
        bad_todo = ToDo()
        self.test_create_todo(bad_todo, authentication, 400)
        bad_todo.userId = authentication.user_id
        self.test_create_todo(bad_todo, authentication, 400)
        bad_todo.name = "todo"
        bad_todo.endInstant = 10000
        self.test_create_todo(bad_todo, authentication, 400)
        bad_todo.startInstant = 9000
        bad_todo.linkedGoalId = -1
        self.test_create_todo(bad_todo, authentication, 400)
        bad_todo.linkedGoalId = None
        bad_todo.startInstant = 11000  # start instant after endInstant
        self.test_create_todo(bad_todo, authentication, 400)

    def test_get_with_malformed_params(self, authentication: Authentication):
        # setup
        good_todo = GO_TO_STORE_TODO
        good_todo.userId = authentication.user_id
        todo_id = self.test_create_todo(good_todo, authentication)
        # test
        self.test_get_todos(good_todo.endInstant, good_todo.startInstant - (60*60*24*5), authentication, 400)
        # cleanup
        self.test_delete_todo(todo_id, authentication)

    def test_update_with_malformed_todos(self, authentication: Authentication):
        # setup
        good_todo = GO_TO_STORE_TODO
        good_todo.userId = authentication.user_id
        good_todo_id = self.test_create_todo(good_todo, authentication)
        # test
        bad_todo = good_todo
        bad_todo.userId = -1
        self.test_update_todo(good_todo_id, bad_todo, authentication, 400)
        bad_todo.userId = authentication.user_id
        bad_todo.startInstant = 100000
        bad_todo.endInstant = 1000
        self.test_update_todo(good_todo_id, bad_todo, authentication, 400)
        bad_todo.startInstant = 5
        #cleanup
        self.test_delete_todo(good_todo_id, authentication)

    def test_call_functions_without_authentication(self, real_authentication: Authentication, another_real_authentication: Authentication):
        # setup
        real_todo = GO_TO_STORE_TODO
        real_todo.userId = real_authentication.user_id
        real_todo_id = self.test_create_todo(real_todo, real_authentication)
        updated_real_todo = real_todo
        updated_real_todo.endInstant += 5000
        # test
        self.test_create_todo(real_todo, another_real_authentication, 401)
        self.test_update_todo(real_todo_id, updated_real_todo, another_real_authentication, 401)
        self.test_delete_todo(real_todo_id, another_real_authentication, 401)

    def test_happy_path(self, authentication: Authentication):
        # create, get, update and delete happy path todos
        start_time_1 = datetime.datetime(year=1999, month=7, day=4)
        start_time_2 = (start_time_1 + relativedelta.relativedelta(years=1, months=1, days=2, hours=10, minutes=5))

        # get todos by day, should return nothing
        events = self.test_get_todos(start_time_1.timestamp(), authentication)
        assert len(events) == 0

        # create todos
        one_day_todos = []
        for i in range(0, 50):
            todo = ToDo(
                name="todo" + str(i),
                userId=authentication.user_id,
                startInstant=start_time_1.timestamp(),
                endInstant=(start_time_1 + datetime.timedelta(days=1)).timestamp(),
            )
            todo.todoId = self.test_create_todo(todo, authentication)
            one_day_todos.append(todo)

        for todo in one_day_todos:
            todo_received = self.test_get_todo(todo.todoId, authentication)
            assert todo.dict() == todo_received.dict()

        todos_received = self.test_get_todos(start_time_1.timestamp(), authentication)[str(int(start_time_1.timestamp()))]
        for todo in one_day_todos:
            assert todos_received.index(todo) >= 0

        # update todos startInstants
        for todo in one_day_todos:
            new_todo = todo
            new_todo.startInstant = start_time_2.timestamp()
            new_todo.endInstant = (start_time_2 + datetime.timedelta(days=1)).timestamp()
            self.test_update_todo(todo.todoId, new_todo, authentication)

        assert (len(
            self.test_get_todos(start_time_2.timestamp(), authentication)[str(int(start_time_2.timestamp()))]) == len(
            one_day_todos))

        # delete todos
        for todo in one_day_todos:
            self.test_delete_todo(todo.todoId, authentication)

        # assert that delete functioned correctly
        for todo in one_day_todos:
            self.test_get_todo(todo.todoId, authentication, 404)

        # create happy path week long todos
        week_long_todos = []
        start_time = start_time_1
        for i in range(0, 50):
            todo = ToDo(
                name="todo" + str(i),
                startInstant=start_time.timestamp(),
                endInstant=(start_time + datetime.timedelta(weeks=1)).timestamp(),
                userId=authentication.user_id
            )
            todo.todoId = self.test_create_todo(todo, authentication)
            start_time += datetime.timedelta(days=1)
            week_long_todos.append(todo)

        # test get todos by day
        day = start_time_1 + datetime.timedelta(days=7)
        todos = self.test_get_todos(day.timestamp(), authentication)[str(int(day.timestamp()))]
        assert len(todos) == 7

        todos = self.test_get_todos(start_time_1.timestamp(),
                                      (start_time_1 + datetime.timedelta(days=60)).timestamp(), authentication)
        assert len(events) == 50
        assert len(events[str(int(start_time_1.timestamp()))]) == 1
        assert len(events[str(int((start_time_1 + datetime.timedelta(days=1)).timestamp()))]) == 2

        # cleanup
        for todo in week_long_todos:
            self.test_delete_todo(todo.todoId, authentication)

    def test_create_todo(self, todo: ToDo, authentication: Authentication,
                         expected_response_code: int = 200):
        todo.userId = authentication.user_id
        res = requests.post(self.todo_url, json=create_authenticated_request_body("todo", todo, authentication))
        compare_responses(res, expected_response_code)
        return res.json()["todo_id"]

    def test_get_todo(self, todo_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.todo_url + "/" + str(todo_id),
                           json=authentication.json())
        compare_responses(res, expected_response_code)
        return res.json()["todo"]

    def test_get_todos(self, start_day: float, authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.get_todos_by_days_list_url, params={"start_day": start_day},
                           json=authentication.json())
        compare_responses(res, expected_response_code)
        return res.json()["todos"]

    def test_get_todos(self, start_day: float, end_day: float, authentication: Authentication,
                       expected_response_code: int = 200):
        res = requests.get(self.get_todos_by_days_range_url, params={"start_day": start_day, "end_day": end_day},
                           json=authentication.json())
        compare_responses(res, expected_response_code)
        return res.json()["todos"]

    def test_update_todo(self, todo_id: int, updated_todo: ToDo, authentication: Authentication,
                         expected_response_code: int = 200):
        updated_todo.userId = authentication.user_id
        res = requests.put(self.todo_url + "/" + str(todo_id),
                           json=create_authenticated_request_body("updated_todo", updated_todo, authentication))
        compare_responses(res, expected_response_code)

    def test_delete_todo(self, todo_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.delete(self.todo_url + "/" + str(todo_id), json=authentication.json())
        compare_responses(res, expected_response_code)
