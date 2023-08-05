from models.ToDo import ToDo
from models.Authentication import Authentication
import requests
from testing.test_scripts.TestingHelperFunctions import *
from ..UserEndpointsTest import UserEndpointsTest
from testing.sample_objects.Users import *
from testing.sample_objects.calendar_items.todos import *


class ToDoTests:

    def __init__(self, base_url: str):
        self.todo_url = base_url + "/todos"
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

        DO_HOMEWORK_TODO.userId = user1_auth.user_id
        DO_HOMEWORK_TODO.todoId = self.test_create_todo(DO_HOMEWORK_TODO, user1_auth)
        res = self.test_get_todo(DO_HOMEWORK_TODO.todoId, user1_auth)
        assert (DO_HOMEWORK_TODO == res)

        GO_TO_STORE_TODO.userId = user1_auth.user_id
        GO_TO_STORE_TODO.todoId = self.test_create_todo(GO_TO_STORE_TODO, user1_auth)
        res = self.test_get_todo(GO_TO_STORE_TODO.todoId, user1_auth)
        assert (GO_TO_STORE_TODO == res)

        READ_SCRIPTURES_TODO.userId = user1_auth.user_id
        READ_SCRIPTURES_TODO.todoId = self.test_create_todo(READ_SCRIPTURES_TODO, user1_auth)
        res = self.test_get_todo(READ_SCRIPTURES_TODO.todoId, user1_auth)
        assert (READ_SCRIPTURES_TODO == res)

        APPLY_FOR_10_JOBS_TODO.userId = user1_auth.user_id
        APPLY_FOR_10_JOBS_TODO.todoId = self.test_create_todo(APPLY_FOR_10_JOBS_TODO, user1_auth)
        res = self.test_get_todo(APPLY_FOR_10_JOBS_TODO.todoId, user1_auth)
        assert (APPLY_FOR_10_JOBS_TODO == res)

        NEW_NAME = "new todo name"
        NEW_DESCRIPTION = "ahhhhhhhhhh!!!!!!!!!!!!!!!\nGRRRRRRRRRRRRRR\n happy happy happy happy joy joy joy what da heck"
        DO_HOMEWORK_TODO.name = NEW_NAME
        DO_HOMEWORK_TODO.description = NEW_DESCRIPTION
        DO_HOMEWORK_TODO.endInstant = datetime.datetime.now() + datetime.timedelta(hours=5)
        self.test_update_todo(DO_HOMEWORK_TODO.todoId, DO_HOMEWORK_TODO, user1_auth)
        res = self.test_get_todo(DO_HOMEWORK_TODO.todoId, user1_auth)
        assert (DO_HOMEWORK_TODO == res)

        NEW_NAME = "new todo name"
        NEW_DESCRIPTION = "ahhhhhhhhhh!!!!!!!!!!!!!!!\nGRRRRRRRRRRRRRR\n happy happy happy happy joy joy joy what da heck"
        DO_HOMEWORK_TODO.name = NEW_NAME
        DO_HOMEWORK_TODO.description = NEW_DESCRIPTION
        DO_HOMEWORK_TODO.endInstant = datetime.datetime.now() + datetime.timedelta(hours=5)
        self.test_update_todo(DO_HOMEWORK_TODO.todoId, DO_HOMEWORK_TODO, user1_auth)
        res = self.test_get_todo(DO_HOMEWORK_TODO.todoId, user1_auth)
        assert (DO_HOMEWORK_TODO == res)

        NEW_NAME = "new todo name"
        NEW_DESCRIPTION = "ahhhhhhhhhh!!!!!!!!!!!!!!!\nGRRRRRRRRRRRRRR\n happy happy happy happy joy joy joy what da heck"
        GO_TO_STORE_TODO.name = NEW_NAME
        GO_TO_STORE_TODO.description = NEW_DESCRIPTION
        GO_TO_STORE_TODO.endInstant = datetime.datetime.now() + datetime.timedelta(hours=5)
        self.test_update_todo(GO_TO_STORE_TODO.todoId, GO_TO_STORE_TODO, user1_auth)
        res = self.test_get_todo(GO_TO_STORE_TODO.todoId, user1_auth)
        assert (GO_TO_STORE_TODO == res)

        NEW_NAME = "new todo name"
        NEW_DESCRIPTION = "ahhhhhhhhhh!!!!!!!!!!!!!!!\nGRRRRRRRRRRRRRR\n happy happy happy happy joy joy joy what da heck"
        READ_SCRIPTURES_TODO.name = NEW_NAME
        READ_SCRIPTURES_TODO.description = NEW_DESCRIPTION
        READ_SCRIPTURES_TODO.endInstant = datetime.datetime.now() + datetime.timedelta(hours=5)
        self.test_update_todo(READ_SCRIPTURES_TODO.todoId, READ_SCRIPTURES_TODO, user1_auth)
        res = self.test_get_todo(READ_SCRIPTURES_TODO.todoId, user1_auth)
        assert (READ_SCRIPTURES_TODO == res)

        self.test_delete_todo(READ_SCRIPTURES_TODO.todoId, user1_auth)
        self.test_get_todo(READ_SCRIPTURES_TODO.todoId, user1_auth, 404)
        READ_SCRIPTURES_TODO.todoId = self.test_create_todo(READ_SCRIPTURES_TODO, user1_auth)
        self.test_create_todo(READ_SCRIPTURES_TODO, user2_auth, 401)

        todos_list: list = self.test_get_todos(time.time(), user1_auth)
        assert (len(todos_list) == 5)
        assert (todos_list.index(GO_TO_STORE_TODO.dict()))
        assert (todos_list.index(READ_SCRIPTURES_TODO.dict()))
        assert (todos_list.index(APPLY_FOR_10_JOBS_TODO.dict()))
        assert (todos_list.index(
            GO_TO_STORE_TODO.dict()))  # check that READ_SCRIPTURES_TODO exists within the list

        todos_tomorrow_list = self.test_get_todos((datetime.datetime.now() + datetime.timedelta(days=1)).timestamp())
        assert (len(todos_tomorrow_list) == 1)
        assert (APPLY_FOR_10_JOBS_TODO.dict() == todos_tomorrow_list[0])

        APPLY_FOR_10_JOBS_TODO.userId = user2_auth.user_id
        APPLY_FOR_10_JOBS_TODO.todoId = self.test_create_todo(APPLY_FOR_10_JOBS_TODO, user2_auth)

        APPLY_FOR_10_JOBS_TODO.userId = user3_auth.user_id
        APPLY_FOR_10_JOBS_TODO.todoId = self.test_create_todo(APPLY_FOR_10_JOBS_TODO, user3_auth)

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
        res = requests.get(self.todo_url, params={"start_day": start_day},
                           json=authentication.json())
        compare_responses(res, expected_response_code)
        return res.json()["todos"]

    def test_get_todos(self, start_day: float, end_day: float, authentication: Authentication, expected_response_code: int = 200):
        res = requests.get(self.todo_url, params={"start_day": start_day, "end_day": end_day},
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