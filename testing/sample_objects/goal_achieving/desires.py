from models.Desire import Desire
import time
import datetime

FAITH_DESIRE = Desire(
  name="Be close to God",
  priorityLevel=1,
  colorR=0,
  colorG=0,
  colorB=0
)
EDUCATION_DESIRE = Desire(
  name="Graduate within a year",
  priorityLevel=1,
  deadline=(datetime.datetime.now() + datetime.timedelta(weeks=52)).timestamp(),
  colorR=0,
  colorG=0,
  colorB=0
)
GET_JOB_DESIRE = Desire(
  name="Get a good job that I enjoy",
  priorityLevel=1,
  colorR=0,
  colorG=0,
  colorB=0
)
