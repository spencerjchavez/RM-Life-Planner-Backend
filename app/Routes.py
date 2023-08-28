# CREATED JUNE OF 2023 BY SPENCER CHAVEZ
from fastapi import FastAPI

from AppMiddleware import AppMiddleware
from app.endpoints import AlertEndpoints, GoalAchievingEndpoints, CalendarToDoEndpoints, RecurrenceEndpoints, \
    CalendarEventEndpoints, UserEndpoints
from testing import TestingRoutes

app = FastAPI()
AppMiddleware.init_db_connection()
app.add_middleware(AppMiddleware)
app.include_router(UserEndpoints.router)
app.include_router(AlertEndpoints.router)
app.include_router(CalendarEventEndpoints.router)
app.include_router(CalendarToDoEndpoints.router)
app.include_router(RecurrenceEndpoints.router)
app.include_router(GoalAchievingEndpoints.router)
app.include_router(TestingRoutes.router)

'''
@app.exception_handler(TimeoutError)
async def timeout_exception_handler(request: Request, exc: TimeoutError):
    print("Received timeout error with the following request params!")
    print(request)
    raise HTTPException(detail="Request timed out", status_code=500)
'''
