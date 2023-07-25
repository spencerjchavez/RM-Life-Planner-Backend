import datetime
from models.Goal import Goal
from models.Goal import Goal
import time

APPLY_FOR_JOB_GOAL = Goal(
  name="apply for 10 jobs",
  howMuch=10,
  measuringUnits="jobs",
  startInstant=time.time(),
  endInstant=(datetime.datetime.now() + datetime.timedelta(days=20)).timestamp()
)
DO_HOMEWORK_GOAL = Goal(
  name="do my homework today",
  howMuch=1,
  startInstant=time.time(),
  endInstant=(datetime.datetime.now() + datetime.timedelta(days=1)).timestamp(),
)
READ_SCRIPTURES_GOAL = Goal(
  name="read the Book of Mormon",
  howMuch=1,
  startInstant=time.time()
)
