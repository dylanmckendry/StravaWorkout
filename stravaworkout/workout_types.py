import operator
from functools import reduce
from statistics import mean

from format_utils import *


class Workout:
    def __init__(self, profile, steps):
        self.profile = profile
        self.steps = steps

    def description(self, include_profile=True, include_warmup_cooldown=True,
                    include_duration=True, include_target=True, include_repeats=True):
        if include_warmup_cooldown:
            steps = self.steps
        else:
            steps = [x for x in self.steps if x.step_type != 'warmup' and x.step_type != 'cooldown']

        if include_profile:
            return 'Workout: {}\nWeight: {}kg'.format(str.join('; ', map(lambda x: x.description(include_duration, include_target, include_repeats), steps)), self.profile)
        else:
            return str.join('; ', map(lambda x: x.description(include_duration, include_target, include_repeats), steps))

    def __str__(self):
        return self.description()


class BaseStep:
    def __init__(self, index, step_type):
        self.index = index
        self.step_type = step_type


class WorkStep(BaseStep):
    def __init__(self,
                 index,
                 step_type,
                 duration_type=None,
                 duration=None,
                 target_type=None,
                 target_zone=None,
                 target_low=None,
                 target_high=None,
                 repeats=None):
        super().__init__(index, step_type)
        self.duration_type = duration_type
        self.duration = duration
        self.target_type = target_type
        self.target_zone = target_zone
        self.target_low = target_low
        self.target_high = target_high
        if repeats is None:
            self.repeats = []
        else:
            self.repeats = repeats

    def repeats_total_distance(self):
        return sum(map(lambda x: x.total_distance(), self.repeats))

    def repeats_avg_total_distance(self):
        return self.repeats_total_distance() / len(self.repeats)

    def repeats_avg_total_time(self):
        return datetime.timedelta(seconds=
                                  sum(map(lambda x: x.total_time().total_seconds(), self.repeats)) / len(self.repeats))

    # TODO: get speed from distance and time?
    def repeats_avg_avg_speed(self):
        return (sum(map(lambda x: x.avg_speed() * x.total_time().total_seconds(), self.repeats))
                / sum(map(lambda x: x.total_time().total_seconds(), self.repeats)))

    def description(self, include_duration=True, include_target=True, include_repeats=True):
        description = ''
        if self.step_type == 'warmup':
            description += f'WU: {format_distance(self.repeats_total_distance())} @ ' \
                           f'{format_speed_as_pace(self.repeats_avg_avg_speed())}'
        elif self.step_type == 'cooldown':
            description += f'CD: {format_distance(self.repeats_total_distance())} @ ' \
                           f'{format_speed_as_pace(self.repeats_avg_avg_speed())}'
        elif self.step_type == 'active' or self.step_type == 'interval' or self.step_type == 'recovery' or self.step_type == 'rest':
            if not include_duration and not include_target and not include_repeats:
                avg_total_distance = sum(map(lambda x: x.total_distance(), self.repeats)) / len(self.repeats)
                avg_speed = sum(map(lambda x: x.avg_speed() * x.total_time(), self.repeats)) / sum(
                    map(lambda x: x.total_time(), self.repeats))

                description += f'{format_distance(avg_total_distance)} @ {format_speed_as_pace(avg_speed)}'
                return description

            if self.duration_type == 'time':
                description += format_time(self.duration)
            elif self.duration_type == 'distance':
                description += format_distance(self.duration)
            elif self.duration_type == 'hr_less_than':
                description += f'<{format_heart_rate(self.duration)}'
            else:
                raise ValueError(f"Unknown duration_type \"{self.duration_type}\" for step_type \"{self.step_type}\"")

            if self.target_type == 'speed':
                description += ': ' + str.join(', ', map(lambda x: x.description(include_distance=False, include_heart_rate=False), self.repeats))
                # description += ' @ {}'.format(format_speed_as_pace((self.target_low + self.target_high) / 2.0))
                # laps = reduce(operator.concat, map(lambda x: x.laps, self.repeats))
                # laps_avg_speeds = map(lambda x: x.avg_speed, laps)

                # avg_speed = sum(map(lambda x: x.avg_speed * x.total_distance, laps)) / sum(
                #     map(lambda x: x.total_distance, laps))
                #
                # avg_heart_rate = sum(map(lambda x: x.avg_heart_rate * x.total_time, laps)) / sum(
                #     map(lambda x: x.total_time, laps))
                # description += ' @ {} ❤ {}'.format(format_speed_as_pace(avg_speed), int(round(avg_heart_rate, 0)))
        else:
            raise ValueError(f"Unknown step_type \"{self.step_type}\"")

        return description

    def __str__(self):
        return self.description()


class RepeatStep(BaseStep):
    def __init__(self, index, step_type, repeat_times, steps):
        super().__init__(index, step_type)
        self.repeat_times = repeat_times
        self.steps = steps

    def description(self, include_duration=True, include_target=True, include_repeats=True):
        return f"{self.repeat_times} * {str.join(' ⇒ ', map(lambda x: x.description(include_duration, include_target, include_repeats), self.steps))}"

    def __str__(self):
        return self.description()


class WorkStepRepeat:
    def __init__(self, laps):
        self.laps = laps

    def total_distance(self):
        return sum(map(lambda x: x.total_distance, self.laps))

    def total_time(self):
        return datetime.timedelta(seconds=sum(map(lambda x: x.total_time.total_seconds(), self.laps)))

    def avg_speed(self):
        return sum(map(lambda x: x.avg_speed * x.total_distance, self.laps)) / self.total_distance()

    def avg_heart_rate(self):
        return (sum(map(lambda x: x.avg_heart_rate * x.total_time.total_seconds(), self.laps))
                / self.total_time().total_seconds())

    def total_ascent(self):
        return sum(map(lambda x: x.total_ascent, self.laps))

    def total_descent(self):
        return sum(map(lambda x: x.total_descent, self.laps))

    def description(self, include_distance=True, include_heart_rate=True):
        description = ''
        if include_distance:
            description += f'{format_distance(self.total_distance())} @ '

        description += f'{format_speed_as_pace(self.avg_speed())}'

        if include_heart_rate:
            description += f' ❤ {format_heart_rate(self.avg_heart_rate())}'

        return description

    def __str__(self):
        return self.description()


class Lap:
    def __init__(self, total_distance, total_time, avg_speed, avg_heart_rate, total_ascent, total_descent):
        self.total_distance = total_distance
        self.total_time = total_time
        self.avg_speed = avg_speed
        self.avg_heart_rate = avg_heart_rate
        self.total_ascent = total_ascent
        self.total_descent = total_descent
