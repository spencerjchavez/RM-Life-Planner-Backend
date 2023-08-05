from models.ToDo import ToDo
from testing.sample_objects.goal_achieving.goals import *

APPLY_FOR_10_JOBS_TODO = ToDo(
  name=APPLY_FOR_JOB_GOAL.name,
  startInstant=time.time(),
  deadline=APPLY_FOR_JOB_GOAL.deadline
)
DO_HOMEWORK_TODO = ToDo(
  name=DO_HOMEWORK_GOAL.name,
  startInstant=time.time(),
  deadline=DO_HOMEWORK_GOAL.deadline
)
READ_SCRIPTURES_TODO = ToDo(
  name=READ_SCRIPTURES_GOAL.name,
  startInstant=time.time(),
  deadline=READ_SCRIPTURES_GOAL.deadline
)
GO_TO_STORE_TODO = ToDo(
  name="go to the store today",
  startInstant=time.time()
)
