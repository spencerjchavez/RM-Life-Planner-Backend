# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

import uvicorn
from fastapi import FastAPI
from endpoints.UserEndpoints import router as users_router
from endpoints.CalendarItemsEndpoint import router as calendar_events_router
from endpoints.GoalAchievingEndpoints import router as goals_router


class Routes:
    def __init__(self):
        app = FastAPI()
        app.include_router(users_router)
        app.include_router(calendar_events_router)
        app.include_router(goals_router)
        uvicorn.run(app, host="localhost", port=8000)
