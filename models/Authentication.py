from pydantic import BaseModel


class Authentication(BaseModel):
    user_id: int
    api_key: str

    @staticmethod
    def from_sql_res(src: dict):
        return Authentication(
            user_id=src["user_id"],
            api_key=src["api_key"]
        )
