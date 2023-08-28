from datetime import datetime


def validate_date(date: str):
    try:
        _ = datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_time(time: str):
    try:
        _ = datetime.strptime(time, "%H:%M:%S")
        return True
    except ValueError:
        return False
