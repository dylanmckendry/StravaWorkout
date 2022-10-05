from format_utils import *


class Workout:
    def __init__(self, steps):
        self.steps = steps

    def __str__(self):
        return str.join('; ', map(str, self.steps))


class BaseStep:
    pass


class WorkStep(BaseStep):
    def __init__(self,
                 step_type,
                 duration_type=None,
                 duration=None,
                 target_type=None,
                 target_low=None,
                 target_high=None,
                 repeats=None):
        self.step_type = step_type
        self.duration_type = duration_type
        self.duration = duration
        self.target_type = target_type
        self.target_low = target_low
        self.target_high = target_high
        if repeats is None:
            self.repeats = []
        else:
            self.repeats = repeats

    def __str__(self):
        description = ''
        if self.step_type == 'warmup':
            description += 'WU'
        elif self.step_type == 'cooldown':
            description += 'CD'
        elif self.step_type == 'active' or self.step_type == 'recovery':
            if self.duration_type == 'time':
                description += format_time(self.duration)
            elif self.duration_type == 'distance':
                description += format_distance(self.duration)
            else:
                raise ValueError(f"Unknown duration_type \"{self.duration_type}\" for step_type \"{self.step_type}\"")

            if self.target_type == 'speed':
                description += ' @ {}'.format(speed_to_pace((self.target_low + self.target_high) / 2.0))
        else:
            raise ValueError(f"Unknown step_type \"{self.step_type}\"")

        return description


class WorkStepRepeat:
    def __init__(self, laps):
        self.laps = laps


class RepeatStep(BaseStep):
    def __init__(self, repeat_times, steps):
        self.repeat_times = repeat_times
        self.steps = steps

    def __str__(self):
        return f"{self.repeat_times} * {str.join(' ⇒ ', map(str, self.steps))}"


class Lap:
    def __init__(self, total_distance, total_time, avg_speed, avg_heart_rate, total_ascent, total_descent):
        self.total_distance = total_distance
        self.total_time = total_time
        self.avg_speed = avg_speed
        self.avg_heart_rate = avg_heart_rate
        self.total_ascent = total_ascent
        self.total_descent = total_descent
