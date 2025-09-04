from datetime import datetime, timedelta

def date_2_str(date: datetime):
    return date.strftime('%Y-%m-%d')

def time_2_str(time: datetime):
    return f"{time.hour:02d}:{time.minute:02d}:{time.second:02d}"

def interval_2_hms(interval:timedelta):
    return total_seconds_2_hms(interval.total_seconds())


def total_seconds_2_hms(total_seconds: float):
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}'
