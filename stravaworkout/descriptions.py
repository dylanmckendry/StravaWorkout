from workout_types import WorkStep, RepeatStep

from format_utils import *


def get_workout_title(workout):
    return get_steps_title(workout.steps, '; ')


def get_steps_title(steps, step_seperator):
    steps = [x for x in steps if x.step_type == 'active' or isinstance(x, RepeatStep)]
    return str.join(step_seperator, map(lambda x: get_step_title(x), steps))


def get_step_title(step):
    if isinstance(step, WorkStep):
        return get_work_step_title(step)
    elif isinstance(step, RepeatStep):
        return f"{step.repeat_times} * {get_steps_title(step.steps, ' ⇒ ')}"
    else:
        raise ValueError(f"type(step) = {type(step)}")


def get_work_step_title(work_step):
    if work_step.step_type == 'active':
        if work_step.duration_type == 'time':
            return format_time(work_step.duration)
        elif work_step.duration_type == 'distance':
            return format_distance(work_step.duration)
        else:
            raise ValueError(f"work_step.duration_type = {work_step.duration_type}")
    else:
        raise ValueError(f"work_step.step_type = {work_step.step_type}")


def get_workout_description(workout):
    descriptions = []
    descriptions.append(get_steps_description(workout.steps, '; '))
    descriptions.append(get_steps_repeats_description(workout.steps))
    return str.join('\n\n', descriptions)


def get_steps_description(steps, step_seperator):
    steps = [x for x in steps if x.step_type != 'warmup' and x.step_type != 'cooldown']
    return str.join(step_seperator, map(lambda x: get_step_description(x), steps))


def get_step_description(step):
    if isinstance(step, WorkStep):
        return get_work_step_description(step)
    elif isinstance(step, RepeatStep):
        return f"{step.repeat_times} * {get_steps_description(step.steps, ' ⇒ ')}"
    else:
        raise ValueError(f"type(step) = {type(step)}")


def get_work_step_description(work_step):
    if work_step.step_type == 'rest':
        return format_time(round_time_to_seconds(work_step.repeats_avg_total_time()))
    elif work_step.step_type == 'recovery' or work_step.step_type == 'active':
        description = ""
        if work_step.step_type == 'recovery' and work_step.duration_type == 'time':
            description += f"{format_time(round_time_to_seconds(work_step.repeats_avg_total_time()))}"
        else:
            description += f"{format_distance(work_step.repeats_avg_total_distance())}"
        description += f" @ {format_speed_as_pace(work_step.repeats_avg_avg_speed())}"
        return description
    else:
        raise ValueError(f"work_step.step_type = {work_step.step_type}")


def get_steps_repeats_description(steps, work_step_prefix=''):
    return str.join('\n', map(lambda x: get_step_repeats_description(x, work_step_prefix), steps))


def get_step_repeats_description(step, work_step_prefix=''):
    if isinstance(step, WorkStep):
        return get_work_step_repeats_description(step, work_step_prefix)
    elif isinstance(step, RepeatStep):
        return f"{get_repeat_step_repeats_description(step)}:\n{get_steps_repeats_description(step.steps, '- ')}"
    else:
        raise ValueError(f"type(step) = {type(step)}")


def get_work_step_repeats_description(work_step, work_step_prefix=''):
    return work_step_prefix + work_step.description()


def get_repeat_step_repeats_description(repeat_step):
    return f"{repeat_step.repeat_times} * {get_steps_description(repeat_step.steps, ' ⇒ ')}"
