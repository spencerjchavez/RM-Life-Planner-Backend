from requests import Response
from test_launcher import sample_users


def compare_responses(response_actual: Response, status_code_expected: int = 200, content_expected: str = None):
    if response_actual.status_code != status_code_expected:
        raise ValueError(
            f"server returned unexpected status code {response_actual.status_code}, ought to have returned {status_code_expected}")
    if response_actual.content != content_expected and content_expected is not None:
        raise ValueError(
            f"server returned unexpected content {response_actual.status_code}, ought to have returned {content_expected}")


def user_id_of_user_as_str(username: str):
    return str(sample_users[username]["authentication"]["user_id"])


def get_authentication_of_user(username: str):
    return sample_users[username]["authentication"]


def print_res(_response: Response):
    print(f"status code = {_response.status_code}; content = {_response.content}")