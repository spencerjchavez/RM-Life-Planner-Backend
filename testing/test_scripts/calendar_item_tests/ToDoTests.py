from models.ToDo import ToDo
from models.Authentication import Authentication
import requests
from testing.test_scripts.TestingHelperFunctions import *


class ToDoTests:

    def __init__(self, todo_url: str):
        self.todo_url = todo_url

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
        return res

    def test_update_todo(self, todo_id: int, updated_todo: ToDo, authentication: Authentication,
                          expected_response_code: int = 200):
        updated_todo.userId = authentication.user_id
        res = requests.put(self.todo_url + "/" + str(todo_id),
                           json=create_authenticated_request_body("updated_todo", updated_todo, authentication))
        compare_responses(res, expected_response_code)

    def test_delete_todo(self, todo_id: int, authentication: Authentication, expected_response_code: int = 200):
        res = requests.delete(self.todo_url + "/" + str(todo_id), json=authentication.json())
        compare_responses(res, expected_response_code)