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


#CREATE TABLE users (user_id INT AUTO_INCREMENT PRIMARY KEY,
#username VARCHAR(20) NOT NULL,
#hashed_password VARCHAR(20) NOT NULL,
#email VARCHAR(30),
#current_api_key VARCHAR(20),
#date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#logged_in BOOLEAN,
#google_calendar_id VARCHAR(84));