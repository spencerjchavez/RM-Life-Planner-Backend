# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from fastapi import FastAPI

from AppMiddleware import AppMiddleware
from app.endpoints import AlertEndpoints, GoalAchievingEndpoints, CalendarToDoEndpoints, RecurrenceEndpoints, \
    CalendarEventEndpoints, UserEndpoints, BaseEndpoint
from testing import TestingRoutes

TEST_MODE = True

app = FastAPI()
AppMiddleware.init_db_credentials(TEST_MODE)
AppMiddleware.init_db_connection()
app.add_middleware(AppMiddleware)
app.include_router(BaseEndpoint.router)
app.include_router(UserEndpoints.router)
app.include_router(AlertEndpoints.router)
app.include_router(CalendarEventEndpoints.router)
app.include_router(CalendarToDoEndpoints.router)
app.include_router(RecurrenceEndpoints.router)
app.include_router(GoalAchievingEndpoints.router)
if TEST_MODE:
    app.include_router(TestingRoutes.router)
