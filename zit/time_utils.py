from datetime import datetime, timedelta


def date_2_str(date: datetime) -> str:
    return date.strftime("%Y-%m-%d")


def time_2_str(time: datetime) -> str:
    return f"{time.hour:02d}:{time.minute:02d}:{time.second:02d}"


def interval_2_hms(interval: timedelta) -> str:
    return total_seconds_2_hms(interval.total_seconds())


def total_seconds_2_hms(total_seconds: float) -> str:
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"


def parse_time(time: str) -> datetime:
    # Parse the time format (HHMM)
    if len(time) > 4 or not time.isdigit():
        raise ValueError("Time must be in HHMM format (e.g., 1200 for noon)")
    if len(time) == 3:
        time = "0" + time
    if len(time) == 2:
        time = time + "00"
    if len(time) == 1:
        time = "0" + time + "00"

    hour = int(time[:2])
    minute = int(time[2:])

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError("Invalid time values")

    return datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)


def verify_date(date: str):
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD format.")


def determine_date(yesterday: bool, date: str) -> str:
    if yesterday:
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    elif date:
        verify_date(date)
        return date
    else:
        return datetime.now().strftime("%Y-%m-%d")
