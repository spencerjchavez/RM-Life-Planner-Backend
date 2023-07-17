from typing import Optional
from pydantic import BaseModel


class User(BaseModel):
    username: Optional[str]
    password: Optional[str]
    salt: Optional[str]
    userId: Optional[str]
    email: Optional[str]
    googleCalendarId: Optional[str]
    dateJoined: Optional[int]

    def get_sql_insert_query(self):
        return "INSERT INTO users (%s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
            return (self.username,
             self.password,
             self.salt,
             self.dateJoined,
             self.email,
             self.googleCalendarId
             )
