from models.ToDo import ToDo
from testing.sample_objects.goal_achieving.goals import *

APPLY_FOR_10_JOBS_TODO = ToDo(
  name=APPLY_FOR_JOB_GOAL.name,
  startInstant=time.time(),
  endInstant=APPLY_FOR_JOB_GOAL.endInstant
)
DO_HOMEWORK_TODO = ToDo(
  name=DO_HOMEWORK_GOAL.name,
  startInstant=time.time(),
  endInstant=DO_HOMEWORK_GOAL.endInstant
)
READ_SCRIPTURES_TODO = ToDo(
  name=READ_SCRIPTURES_GOAL.name,
  startInstant=time.time(),
  endInstant=READ_SCRIPTURES_GOAL.endInstant
)
GO_TO_STORE_TODO = ToDo(
  name="go to the store today",
  startInstant=time.time()
)
