from typing import Optional
from pydantic import BaseModel
from models.SQLColumnNames import *


class User(BaseModel):
    username: Optional[str]
    password: Optional[str]
    hashedPassword: Optional[bytes]
    salt: Optional[bytes]
    userId: Optional[int]
    email: Optional[str]
    googleCalendarId: Optional[str]
    dateJoined: Optional[float]

    def get_sql_insert_query(self):
        return "INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (None,
                self.username,
                self.hashedPassword,
                self.salt,
                self.dateJoined,
                self.email,
                self.googleCalendarId
                )

    @staticmethod
    def from_sql_res(src: dict):
        return User(username=src[USERNAME],
                    dateJoined=src["date_joined"],
                    email=src[EMAIL],
                    googleCalendarId=src[GOOGLE_CALENDAR_ID]
                    )
