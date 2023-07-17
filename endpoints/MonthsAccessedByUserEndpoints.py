from datetime import datetime, timedelta
from mysql.connector.connection import MySQLCursor
from models.Authentication import Authentication
from endpoints.RecurrenceEndpoints import RecurrenceEndpoints
from models.SQLColumnNames import SQLColumnNames as _
from dateutil import rrule
from dateutil.rrule import rrulestr
from dateutil import relativedelta
from endpoints.CalendarEventEndpoints import CalendarEventEndpoints
from endpoints.CalendarToDoEndpoints import CalendarToDoEndpoints
from endpoints.GoalAchievingEndpoints import GoalAchievingEndpoint
from models.CalendarEvent import CalendarEvent
from models.ToDo import ToDo
from models.Goal import Goal
from models.Recurrence import Recurrence

class MonthsAccessedByUser:
    # TODO: DOUBLE CHECK THAT occurrence VARIABLES ARE ACTUALLY OF TYPE datetime.

    cursor: MySQLCursor
    cache: {int: {int: {int: bool}}} = {}  # user_id, year, month, true if specified month has been accessed by user

    @staticmethod
    def get_months_accessed_by_user(user_id):
        MonthsAccessedByUser.cursor.execute("SELECT month, year FROM months_accessed_by_user WHERE user_id = %s", user_id)
        res = MonthsAccessedByUser.cursor.fetchall()
        year_month_tuples = []
        for row in res:
            year = row["year"]
            month = row["month"]
            year_month_tuples.append((year, month))
            MonthsAccessedByUser.cache.setdefault(user_id, {}).setdefault(year, {})[month] = True
        return year_month_tuples

    @staticmethod
    def register_month_accessed_by_user(authentication: Authentication, year: int, month: int):
        if not MonthsAccessedByUser.cache.get(authentication.user_id, {}).get(year, {}).get(month, False):
            MonthsAccessedByUser.cursor.execute("SELECT * FROM months_accessed_by_user WHERE (user_id, year, month) = (%s, %s, %s)", (authentication.user_id, year, month))
            if MonthsAccessedByUser.cursor.fetchone() is None:  # month has not been accessed before
                MonthsAccessedByUser.__generate_recurrence_instances_for_month(authentication, year, month)
                MonthsAccessedByUser.cursor.execute("INSERT INTO months_accessed_by_user (%s, %s, %s)", (authentication.user_id, year, month))
            MonthsAccessedByUser.cache.setdefault(authentication.user_id, {}).setdefault(year, {})[month] = True

    @staticmethod
    def __generate_recurrence_instances_for_month(authentication: Authentication, year: int, month: int):
        MonthsAccessedByUser.cursor.execute("SELECT * FROM recurrences WHERE user_id = %s", (authentication.user_id,))
        res = MonthsAccessedByUser.cursor.fetchall()
        for row in res:
            rrule_str = row[_.RRULE_STRING]
            rule = rrulestr(rrule_str)
            start_dt = datetime(year=year, month=month, day=1, hour=0, minute=0, second=0,microsecond=0)
            end_dt = start_dt + relativedelta.relativedelta(months=1) - timedelta(minutes=1)
            occurrences = rule.between(after=start_dt, before=end_dt, inc=True)

            for occurrence in occurrences:
                # is occurrence a datetime?? hopefully...
                MonthsAccessedByUser.__generate_recurrence_instance(authentication, res, occurrence)


    @staticmethod
    def __generate_recurrence_instance(authentication: Authentication, recurrence_dict: {}, dt: datetime):
        goal_id = None
        if recurrence_dict[_.RECURRENCE_GOAL_NAME] is not None:
            goal = Goal()
            goal.name = recurrence_dict[_.RECURRENCE_GOAL_NAME]
            goal.userId = recurrence_dict["user_id"]
            goal.desireId = recurrence_dict[_.RECURRENCE_GOAL_DESIRE_ID]
            goal.howMuch = recurrence_dict[_.RECURRENCE_GOAL_HOW_MUCH]
            goal.measuringUnits = recurrence_dict[_.RECURRENCE_GOAL_MEASURING_UNITS]
            goal.timeframe = recurrence_dict[_.RECURRENCE_GOAL_TIMEFRAME]
            goal.startInstant = dt.timestamp()
            goal.recurrenceId = recurrence_dict[_.RECURRENCE_ID]
            goal_id = GoalAchievingEndpoint.create_goal(authentication, goal)[0]["goal_id"]

        todo_id = None
        if recurrence_dict[_.RECURRENCE_TODO_NAME] is not None:
            todo = ToDo()
            todo.name = recurrence_dict[_.RECURRENCE_TODO_NAME]
            todo.recurrenceId = recurrence_dict[_.RECURRENCE_ID]
            todo.userId = recurrence_dict[_.USER_ID]
            todo.startInstant = dt.timestamp()
            todo.timeframe = recurrence_dict[_.RECURRENCE_TODO_TIMEFRAME]
            if goal_id is not None:
                todo.linkedGoalId = goal_id
            todo_id = CalendarToDoEndpoints.create_todo(authentication, todo)[0]["todo_id"]

        if recurrence_dict[_.RECURRENCE_EVENT_NAME] is not None:
            event = CalendarEvent()
            event.name = recurrence_dict[_.RECURRENCE_EVENT_NAME]
            event.description = recurrence_dict[_.RECURRENCE_EVENT_DESCRIPTION]
            event.startInstant = dt.timestamp()
            event.endInstant = event.startInstant + recurrence_dict[_.RECURRENCE_EVENT_DURATION]
            event.duration = recurrence_dict[_.RECURRENCE_EVENT_DURATION]
            event.userId = authentication.user_id
            event.recurrenceId = recurrence_dict[_.RECURRENCE_ID]
            if goal_id is not None:
                event.linkedGoalId = goal_id
            if todo_id is not None:
                event.linkedTodoId = todo_id
            CalendarEventEndpoints.create_calendar_event(authentication, event)

    @staticmethod
    def generate_recurrence_instances_for_new_recurrence(authentication: Authentication, recurrence: Recurrence):
        year_month_tuples = MonthsAccessedByUser.get_months_accessed_by_user(authentication.user_id)
        for year, month in year_month_tuples:
            rule = rrule.rrulestr(recurrence.rruleString)
            start_dt = datetime(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_dt = start_dt + relativedelta.relativedelta(months=1) - timedelta(minutes=1)
            if end_dt.timestamp() >= recurrence.startInstant:  # if within recurrence timeframe, generate instances, else pass
                occurrences = rule.between(after=start_dt, before=end_dt, inc=True)
                for occurrence in occurrences:
                    if occurrence.timestamp() >= recurrence.startInstant:
                        MonthsAccessedByUser.__generate_recurrence_instance(authentication, recurrence.__dict__, occurrence)

    @staticmethod
    def delete_recurrence_instances(authentication: Authentication, recurrence_id: int, after: float, inclusive: bool):
        RecurrenceEndpoints.get_recurrence(authentication, recurrence_id)  # authenticate
        MonthsAccessedByUser.cursor.execute("DELETE FROM goals WHERE recurrence_id = %s AND %s %s %s;",
                                            (recurrence_id, _.START_INSTANT, ">=" if inclusive else ">", after))
        MonthsAccessedByUser.cursor.execute("DELETE FROM todos WHERE recurrence_id = %s AND %s %s %s;",
                                            (recurrence_id, _.START_INSTANT, ">=" if inclusive else ">", after))
        MonthsAccessedByUser.cursor.execute("DELETE FROM events WHERE recurrence_id = %s AND %s %s %s",
                                            (recurrence_id, _.START_INSTANT, ">=" if inclusive else ">", after))
        RecurrenceEndpoints.set_recurrence_end(authentication, recurrence_id, after)

    @staticmethod
    def update_recurrence_instances(authentication: Authentication, recurrence_id: int, after: float, inclusive: bool):
