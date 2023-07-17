from pydantic import BaseModel


class Authentication(BaseModel):
    user_id: int
    api_key: str
