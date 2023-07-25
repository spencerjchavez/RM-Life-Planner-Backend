from typing import Any

from requests import Response
from models.Authentication import Authentication


def compare_responses(response_actual: Response, status_code_expected: int = 200, content_expected: str = None):
    if response_actual.status_code != status_code_expected:
        raise ValueError(
            f"server returned unexpected status code {response_actual.status_code}, ought to have returned {status_code_expected}\nContent returned:\n{response_actual.content}")
    if response_actual.content != content_expected and content_expected is not None:
        raise ValueError(
            f"server returned unexpected content {response_actual.status_code}, ought to have returned {content_expected}.")
def create_authenticated_request_body(parameter_name: str, parameter_data: Any, authentication: Authentication):
    return {parameter_name: parameter_data.__dict__,
            "authentication": authentication.__dict__}
