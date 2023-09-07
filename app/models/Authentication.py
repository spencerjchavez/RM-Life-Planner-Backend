from typing import Any

from pydantic import BaseModel


class Authentication(BaseModel):
    user_id: int
    api_key: str

    def __init__(self, user_id: int, api_key: str):
        super().__init__(user_id=user_id, api_key=api_key)

    @staticmethod
    def from_sql_res(src: dict):
        return Authentication(
            user_id=src["user_id"],
            api_key=src["api_key"]
        )
