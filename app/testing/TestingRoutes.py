from fastapi import APIRouter
from app.db_connections import DBConnections
from app.endpoints import RecurrenceEndpoints, UserEndpoints, GoalAchievingEndpoints, CalendarEventEndpoints
from app.models.Authentication import Authentication
from app.models.CalendarEvent import CalendarEvent
from app.models.Desire import Desire
from app.models.Goal import Goal
from app.models.User import User

router = APIRouter()


@router.post("/api/testing/reset_tables")
def reset_tables():
    conn = DBConnections.get_db_connection()
    cursor = conn.cursor()
    try:
        with open("testing/init_tables_script.sql", 'r') as file:
            script = file.read()
            file.close()
            for _ in cursor.execute(script, multi=True):
                pass
            _ = cursor.fetchall()
            RecurrenceEndpoints.months_accessed_cache = {}
            return {"message": "success"}
    finally:
        conn.close()


@router.post("/api/testing/dummy_data")
def dummy_data():
    reset_tables()
    # make a user
    USER1 = User(
        username="spencer",
        password="password",
        email="email@realemail.com"
    )
    res = UserEndpoints.register_user(USER1)
    authentication = res["authentication"]
    user_id = authentication.user_id
    # desires
    desire1 = Desire(
        name="Be a good father",
        userId=user_id,
        dateCreated="2000-08-15"
    )
    desire2 = Desire(
        name="Get a job",
        userId=user_id,
        dateCreated="2000-08-15"
    )
    desire1Id = GoalAchievingEndpoints.create_desire(authentication, desire1)["desire_id"]
    desire2Id = GoalAchievingEndpoints.create_desire(authentication, desire2)["desire_id"]

    # goals
    goal1 = Goal(
        desireId=desire1Id,
        userId=authentication.user_id,
        name="Play with kids",
        howMuch=5,
        startDate="2024-02-10",
        deadlineDate="2024-02-13",
        priorityLevel=1
    )
    goal2 = Goal(
        desireId=desire1Id,
        userId=authentication.user_id,
        name="Have family dinner",
        howMuch=3,
        startDate="2024-02-10",
        deadlineDate="2024-02-13",
        priorityLevel=2
    )
    goal3 = Goal(
        desireId=desire2Id,
        userId=authentication.user_id,
        name="Apply to 5 jobs weekly",
        howMuch=5,
        startDate="2024-02-10",
        deadlineDate="2024-02-13",
        priorityLevel=1
    )
    goal1Id = GoalAchievingEndpoints.create_goal(authentication, goal1)["goal_id"]
    goal2Id = GoalAchievingEndpoints.create_goal(authentication, goal2)["goal_id"]
    goal3Id = GoalAchievingEndpoints.create_goal(authentication, goal3)["goal_id"]

    # events
    event1 = CalendarEvent(
        name="play with kids",
        userId=authentication.user_id,
        startDate="2024-02-13",
        startTime="11:30:55",
        endDate="2024-02-13",
        endTime="12:30:55",
        linkedGoalId=goal1Id,
        howMuchAccomplished=1
    )
    event2 = CalendarEvent(
        name="play with kids",
        userId=authentication.user_id,
        startDate="2024-02-12",
        startTime="12:30:55",
        endDate="2024-02-12",
        endTime="13:30:55",
        linkedGoalId=goal1Id,
        howMuchAccomplished=1
    )
    event3 = CalendarEvent(
        name="have family dinner",
        userId=authentication.user_id,
        startDate="2024-02-12",
        startTime="15:30:55",
        endDate="2024-02-12",
        endTime="17:30:55",
        linkedGoalId=goal2Id,
        howMuchAccomplished=2
    )
    event4 = CalendarEvent(
        name="apply for jobs",
        userId=authentication.user_id,
        startDate="2024-02-13",
        startTime="8:30:55",
        endDate="2024-02-13",
        endTime="10:30:55",
        linkedGoalId=goal3Id,
        howMuchAccomplished=3
    )
    event1Id = CalendarEventEndpoints.create_calendar_event(authentication, event1)
    event1Id = CalendarEventEndpoints.create_calendar_event(authentication, event2)
    event1Id = CalendarEventEndpoints.create_calendar_event(authentication, event3)
    event1Id = CalendarEventEndpoints.create_calendar_event(authentication, event4)

