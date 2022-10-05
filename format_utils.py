import datetime


def round_time_to_seconds(time):
    return datetime.timedelta(seconds=round(time.total_seconds(), 0))


def speed_to_pace(speed):
    pace = round_time_to_seconds(datetime.timedelta(minutes=16.666666667 / speed))
    return '{}'.format(format_time(pace))


def format_time(time):
    time_str = str(time)
    time_total_seconds = time.total_seconds()
    if time_total_seconds >= 1 * 60 * 60:
        return time_str
    elif time_total_seconds >= 1 * 10 * 60:
        return time_str[2:]
    else:
        return time_str[3:]


def format_distance(distance):
    if distance >= 1000:
        return '{:.2f}km'.format(distance / 1000.0)
    else:
        return '{:.2f}m'.format(distance)
