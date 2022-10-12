import argparse
import configparser
import datetime
import logging
import os
import re
import sys
import tempfile

import fitdecode

from stravalib import Client
from stravaweblib import WebClient

from descriptions import get_workout_title, get_workout_description
from workout_types import Workout, WorkStep, WorkStepRepeat, Lap, RepeatStep

__log__ = logging.getLogger(__name__)

CONFIG_FILE = os.path.join(
    os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config')),
    'strava-workout.conf'
)


def print_fields(fields):
    for field in fields:
        print(f"{field.name} = {field.value} ({field.raw_value})")
    print()


def get_frame_field_by_name(frame, field_name):
    for field in frame.fields:
        if field.name == field_name:
            return field

    raise ValueError(f"Field \"{field_name}\" not found in frame")


def get_workout_step_indexes(workout_steps):
    for workout_step in workout_steps:
        if isinstance(workout_step, WorkStep):
            yield workout_step.index
        elif isinstance(workout_step, RepeatStep):
            for workout_step_index in get_workout_step_indexes(workout_step.steps):
                yield workout_step_index


def get_workout_step_by_index(workout_steps, index):
    for workout_step in workout_steps:
        if isinstance(workout_step, WorkStep):
            if workout_step.index == index:
                return workout_step
        elif isinstance(workout_step, RepeatStep):
            workout_step = get_workout_step_by_index(workout_step.steps, index)
            if workout_step is not None:
                return workout_step
        else:
            raise ValueError()

    return None


# TODO: check workout exists or return None, check it is running
def create_workout(file):
    user_profile = None
    lap_frames = []
    workout_step_frames = []

    with fitdecode.FitReader(file) as fit:
        for frame in fit:
            if frame.frame_type == fitdecode.FIT_FRAME_DATA:
                if frame.name == 'lap':
                    lap_frames.append(frame)
                elif frame.name == 'workout_step':
                    workout_step_frames.append(frame)
                elif frame.name == 'user_profile':
                    assert user_profile is None
                    user_profile = frame

    if len(workout_step_frames) == 0:
        return None

    workout_steps = []

    for frame in workout_step_frames:
        workout_step_type = get_frame_field_by_name(frame, 'intensity').value
        workout_step_duration_type = get_frame_field_by_name(frame, 'duration_type').value

        # TODO: need to see how this works in other files
        if workout_step_type is None and workout_step_duration_type == 'repeat_until_steps_cmplt':
            num_steps_to_repeat = get_frame_field_by_name(frame, 'message_index').value - \
                                  get_frame_field_by_name(frame, 'duration_step').value
            assert num_steps_to_repeat > 0

            workout_step = RepeatStep(get_frame_field_by_name(frame, 'message_index').value,
                                      workout_step_type,
                                      get_frame_field_by_name(frame, 'repeat_steps').value,
                                      workout_steps[-num_steps_to_repeat:])

            workout_steps = workout_steps[:len(workout_steps) - num_steps_to_repeat]

        else:
            workout_step = WorkStep(get_frame_field_by_name(frame, 'message_index').value,
                                    workout_step_type,
                                    workout_step_duration_type,
                                    None,
                                    get_frame_field_by_name(frame, 'target_type').value)

            if workout_step.duration_type == 'time':
                workout_step.duration = datetime.timedelta(
                    seconds=get_frame_field_by_name(frame, 'duration_time').value)
            elif workout_step.duration_type == 'distance':
                workout_step.duration = get_frame_field_by_name(frame, 'duration_distance').value
            elif workout_step.duration_type == 'hr_less_than':
                workout_step.duration = get_frame_field_by_name(frame, 'duration_hr').value - 100  # TODO: 210 vs 110
            elif workout_step.duration_type == 'open':
                pass
            elif workout_step.duration_type is None:
                pass
            else:
                raise ValueError(f"Unknown duration_type \"{workout_step.duration_type}\"")

            if workout_step.target_type == 'speed':
                workout_step.target_low = get_frame_field_by_name(frame, 'custom_target_speed_low').value
                workout_step.target_high = get_frame_field_by_name(frame, 'custom_target_speed_high').value
            elif workout_step.target_type == 'heart_rate':
                workout_step.target_zone = get_frame_field_by_name(frame, 'target_hr_zone').value
                workout_step.target_low = get_frame_field_by_name(frame, 'custom_target_heart_rate_low').value
                workout_step.target_high = get_frame_field_by_name(frame, 'custom_target_heart_rate_high').value
            elif workout_step.target_type == 'open':
                pass
            elif workout_step.target_type is None:
                pass
            else:
                raise ValueError(f"Unknown target_type \"{workout_step.target_type}\"")

        workout_steps.append(workout_step)

    # TODO: what to do if end of workout?
    last_workout_step_index = None
    for frame in lap_frames:
        workout_step = get_workout_step_by_index(workout_steps, get_frame_field_by_name(frame, 'wkt_step_index').value)

        # TODO: end of workout?
        if workout_step is None:
            break

        if workout_step.index != last_workout_step_index:
            last_workout_step_index = workout_step.index
            workout_step.repeats.append(WorkStepRepeat([]))

        workout_step.repeats[-1].laps.append(Lap(
            get_frame_field_by_name(frame, 'total_distance').value,
            datetime.timedelta(seconds=get_frame_field_by_name(frame, 'total_elapsed_time').value),
            get_frame_field_by_name(frame, 'enhanced_avg_speed').value,
            get_frame_field_by_name(frame, 'avg_heart_rate').value,
            get_frame_field_by_name(frame, 'total_ascent').value,
            get_frame_field_by_name(frame, 'total_descent').value,
        ))

    return Workout(get_frame_field_by_name(user_profile, 'weight').value, workout_steps)


def print_workout_description():
    workout = Workout(None, [
        WorkStep(0, 'warmup'),
        RepeatStep(3, 'repeat_until_steps_cmplt', 4, [
            WorkStep(1, 'active', 'distance', 2000, 'speed', None, 4000, 4167),
            WorkStep(2, 'recovery', 'time', 300000),
        ]),
        WorkStep(4, 'cooldown'),
    ])

    print(workout)


def main():
    # workout = create_workout('C:\\Users\\dylan\\Downloads\\Afternoon_Run 2km.fit')
    # print(workout.description(False, False, False, False, False))
    # return

    parser = argparse.ArgumentParser(
        description='Create workout descriptions from your FIT files.'
    )
    parser.add_argument("--config", nargs="?", type=argparse.FileType('rt'),
                        default=CONFIG_FILE,
                        help="The config file to use (default: %(default)s)")
    args = parser.parse_args()

    config_data = args.config.read()
    config = configparser.ConfigParser()
    config.read_string(config_data)

    client_id = int(config['api']['client_id'])
    client_secret = config['api']['client_secret']
    refresh_token = config['api']['refresh_token']
    email = config['user']['email']
    password = config['user']['password']

    tokens = Client().refresh_access_token(client_id, client_secret, refresh_token)
    if tokens['refresh_token'] != refresh_token:
        refresh_token = tokens['refresh_token']
        config_path = args.config.name
        try:
            if config_path == "<stdin>":
                raise FileNotFoundError("Cannot write to config file passed via stdin")
            with open(config_path, 'w') as f:
                new_config = re.sub(
                    r'^(\s*refresh_token\s*=\s*)\w+(.*)$',
                    r'\1{}\2'.format(refresh_token),
                    config_data
                )
                f.write(new_config)
        except OSError:
            __log__.warning(
                "Failed to automatically update refresh token in the config file - "
                "please update it manually", exc_info=True
            )
            __log__.warning("New refresh token is '%s'", refresh_token)

    access_token = tokens['access_token']

    client = WebClient(access_token=access_token, email=email, password=password)

    activities = client.get_activities(limit=1)

    for activity in activities:
        if activity.type != 'Run':
            continue

        data = client.get_activity_data(activity.id)

        if not data.filename.endswith('.fit'):
            continue

        __log__.info("Downloading activity %s (%s)", activity, data.filename)
        with tempfile.TemporaryFile() as file:
            file.writelines(data.content)
            file.seek(0, 0)
            activity_workout = create_workout(file)

            if activity_workout is not None:
                name = get_workout_title(activity_workout)
                description = get_workout_description(activity_workout)
                print(name)
                print(description)
                print()
                description += "\n\n Work in progress @ https://github.com/dylanmckendry/StravaWorkout"
                client.update_activity(activity.id, name=name, description=description)

    print(activities)


if __name__ == '__main__':
    main()

