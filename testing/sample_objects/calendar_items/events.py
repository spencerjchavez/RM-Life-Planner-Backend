import datetime

from models.CalendarEvent import CalendarEvent
from testing.sample_objects.goal_achieving.goals import *
from testing.sample_objects.calendar_items.todos import *

GO_TO_STORE_EVENT = CalendarEvent(
  name=GO_TO_STORE_TODO.name,
  description="go to the walmart in springville",
  startInstant=datetime.datetime.now(),
  endInstant=(datetime.datetime.now() + datetime.timedelta(minutes=20)).timestamp()
)
READ_SCRIPTURES_EVENT = CalendarEvent(
  name=READ_SCRIPTURES_GOAL.name,
  startInstant=(datetime.datetime.now() + datetime.timedelta(minutes=20)).timestamp(),
  endInstant=(datetime.datetime.now() + datetime.timedelta(minutes=20)).timestamp()
)
APPLY_FOR_JOB_EVENT = CalendarEvent(
  name=APPLY_FOR_JOB_GOAL.name,
  description="apply for a job",
  startInstant=(datetime.datetime.now() + datetime.timedelta(minutes=80)).timestamp(),
  endInstant=(datetime.datetime.now() + datetime.timedelta(minutes=60)).timestamp()
)
DO_HOMEWORK_EVENT = CalendarEvent(
  name=DO_HOMEWORK_GOAL.name,
  description="calc time babyyyyyyyyy",
  startInstant=(datetime.datetime.now() + datetime.timedelta(minutes=20)).timestamp(),
  endInstant=(datetime.datetime.now() + datetime.timedelta(minutes=20)).timestamp()
)
WEEK_LONG_VACATION_EVENT = CalendarEvent(
  name="go to mexico for a week",
  startInstant=time.time(),
  endInstant=(datetime.datetime.now() + datetime.timedelta(days=7)).timestamp()
)

