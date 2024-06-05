from pydantic import BaseModel
from app.extras.SQLColumnNames import *


class UserPreferences(BaseModel):
    userId: int
    veryHighPriorityColor: str
    highPriorityColor: str
    mediumPriorityColor: str
    lowPriorityColor: str

    def get_sql_events_insert_query(self):
        return "INSERT INTO user_preferences VALUES (%s, %s, %s, %s, %s);"

    def get_sql_insert_params(self):
        return (self.userId,
                self.veryHighPriorityColor,
                self.highPriorityColor,
                self.mediumPriorityColor,
                self.lowPriorityColor)

    @staticmethod
    def from_sql_res(src: dict):
        return UserPreferences(
            userId = src[USER_ID],
            veryHighPriorityColor = src["very_high_priority_color"],
            highPriorityColor = src["high_priority_color"],
            mediumPriorityColor = src["medium_priority_color"],
            lowPriorityColor = src["low_priority_color"]
        )