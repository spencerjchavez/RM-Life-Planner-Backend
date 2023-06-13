# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

import uvicorn
from dateutil.rrule import rrulestr
from fastapi import FastAPI
from mysql.connector.cursor import MySQLCursor
from users.UsersEndpoint import router as users_router
from calendar1.events.CalendarEventsEndpoint import router as calendar_events_router
from goal_achieving.GoalAchievingEndpoint import router as goals_router


class Routes:
    def __init__(self):
        app = FastAPI()
        app.include_router(users_router)
        app.include_router(calendar_events_router)
        app.include_router(goals_router)
        uvicorn.run(app, host="localhost", port=8000)