import datetime

from models.Recurrence import Recurrence
from models.ToDo import ToDo
from models.Goal import Goal
import time

WEEKLY_MEETING = Recurrence(
  rruleString="FREQ=WEEKLY;INTERVAL=1",
  startInstant=time.time(),

  eventName="Fun meeting!",
  eventDescription ="no notes needed, i am too goated for such things\n\n\nlol jk",
  eventDuration=60*60
)

CHURCH_RECURRENCE = Recurrence(
  rruleString="FREQ=WEEKLY;INTERVAL=1",
  startInstant=time.time(),

  eventName ="church time",
  eventDuration = 60*60*2
)
DAILY_BREAKFAST = Recurrence(
  rruleString="FREQ=DAILY;INTERVAL=1",
  startInstant=time.time(),

  eventName ="eat breakfast",
  eventDescription ="",
  eventDuration = 60*30
)
SERVE_SOMEONE_SUN_FRI_RECURRENCE = Recurrence(
  rruleString="FREQ=WEEKLY;INTERVAL=1;BYDAY=SU,FR",
  startInstant=time.time(),

  todoName="serve someone today",
  todoTimeframe=ToDo.Timeframe.DAY
)
DO_SOMETHING_USEFUL_MONTHLY_RECURRENCE = Recurrence(
  rruleString="FREQ=MONTHLY;INTERVAL=1;BYMONTHDAY=1",
  startInstant=time.time(),

  todoName="Do something useful this month",
  todoTimeframe=ToDo.Timeframe.MONTH
)
MY_BIRTHDAY_RECURRENCE= Recurrence(
  rruleString="FREQ=YEARLY;INTERVAL=1",
  startInstant=datetime.datetime(year=1999, month=7, day=4).timestamp(),

  eventName="my birthday!",
  duration=60*60*24
)
EAT_VEGETABLES_DAILY_RECURRENCE = Recurrence(
  rruleString="FREQ=DAILY;INTERVAL=1",
  startInstant=time.time(),

  goalName="Eat vegetables daily",
  goalHowMuch=1,
  goalTimeframe=Goal.Timeframe.DAY,

  todoName="eat vegetables",
  todoTimeframe=ToDo.Timeframe.DAY,
)
GO_TO_THE_TEMPLE_MONTHLY_RECURRENCE = Recurrence(
  rruleString="FREQ=MONTHLY;INTERVAL=1",
  startInstant=time.time(),

  goalName="go to the temple every month!",
  goalHowMuch=1,
  goalTimeframe=Goal.Timeframe.DAY,

  todoName="go to the temple",
  todoTimeframe=ToDo.Timeframe.DAY
)
PRAY_DAILY_RECURRENCE = Recurrence(
  rruleString="FREQ=DAILY;INTERVAL=1",
  startInstant=time.time(),

  goalName="Pray every day",
  goalHowMuch=1,
  goalTimeframe=Goal.Timeframe.DAY,

  todoName="Pray",
  todoTimeframe=ToDo.Timeframe.DAY,

  eventName="pray",
  eventDuration=60*15
)
TRIM_THE_TREES_RECURRENCE = Recurrence(
  rruleString="FREQ=MONTHLY;INTERVAL=1",
  startInstant=time.time(),

  goalName="Trim the trees monthly",
  goalHowMuch=5,
  goalMeasuringUnits="trees",
  goalTimeframe=Goal.Timeframe.MONTH,

  todoName="trim the trees",
  todoTimeframe=ToDo.Timeframe.MONTH,

  eventName="trim the trees",
  eventDescription="all 5 of them",
  eventDuration=60*60,
)
