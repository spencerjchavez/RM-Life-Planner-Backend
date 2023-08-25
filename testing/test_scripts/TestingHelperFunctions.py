from typing import Any

from requests import Response
from models.Authentication import Authentication


def compare_responses(response_actual: Response, status_code_expected: int = 200, content_expected: str = None):
    assert response_actual.status_code == status_code_expected, \
        f"server returned unexpected status code {response_actual.status_code}, ought to have returned {status_code_expected}\nContent returned:\n{response_actual.content}"
    assert response_actual.content == content_expected or content_expected is None, \
        f"server returned unexpected content {response_actual.status_code}, ought to have returned {content_expected}."


def create_authenticated_request_body(parameter_name: str, parameter_data: Any, authentication: Authentication):
    return {parameter_name: parameter_data.__dict__,
            "authentication": authentication.__dict__}
