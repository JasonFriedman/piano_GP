#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import defaultdict

import task_generation.generator as generator
from task_generation.practice_modes import PracticeMode
from task_generation.task_data import TaskData
from task_generation.task_parameters import TaskParameters

"""
What is a task? 

in regards to how the score is generated:
    - task parameters (might be sidestepped by loading midi)

in regards to playing it:
    - midi file (with metronome etc)
    - musicxml file (finger numbers)

after it was played:
    - errors

"""


class TargetTask:

    def __init__(self, task_data: TaskData):
        self.task_data = task_data

        # FIXME :  add comment what is subtask_queue
        self.subtask_queue = [("TARGET", self.task_data)]  # type: list[(str, TaskData)]
        self.subtask_queue_index = 0

        self.error_dict = defaultdict(list)  # map subtask to list of error

    @staticmethod
    def from_task_parameters(task_parameters: TaskParameters):
        task_data = generator.generate_task(task_parameters)
        return TargetTask(task_data)

    def queue_practice_mode(self, practice_mode):
        new_task_data, description = apply_practice_mode(self.task_data, practice_mode)
        self.subtask_queue_index = len(self.subtask_queue)
        self.subtask_queue.extend(zip(description, new_task_data))

    def single_target_eval_at_end(self):
        self.subtask_queue_index = 0
        target_eval = ("TARGET", self.task_data)
        while target_eval in self.subtask_queue:
            self.subtask_queue.remove(target_eval)
        self.subtask_queue.append(target_eval)

    def current_task_data(self) -> TaskData:
        print("(TARGET TASK) subtask queue:", self.subtask_queue, "[", self.subtask_queue_index,
              "]")
        return self.subtask_queue[self.subtask_queue_index][1]  # its a name, data tuple

    def register_error(self, error, task_data=None):
        task_data = task_data or self.current_task_data()
        self.error_dict[task_data].append(error)

    def next_subtask_exists(self) -> bool:
        return self.subtask_queue_index < len(self.subtask_queue) - 1

    def next_subtask(self) -> TaskData:
        if not self.next_subtask_exists():
            raise IndexError()

        self.subtask_queue_index += 1
        return self.current_task_data()

    def previous_subtask_exists(self) -> bool:
        return self.subtask_queue_index > 0

    def previous_subtask(self) -> TaskData:
        if not self.previous_subtask_exists():
            raise IndexError()

        self.subtask_queue_index -= 1
        return self.current_task_data()


def apply_practice_mode(task_data: TaskData, practice_mode: PracticeMode) -> tuple[list[object], list[str]]:
    from task_generation.generator import TaskNote

    if practice_mode == PracticeMode.IDENTITY:
        new_td = task_data.asdict()
        new_td["practice_mode"] = PracticeMode.IDENTITY
        return [TaskData(**new_td)], ["IDENTITY"]

    if practice_mode == PracticeMode.RIGHT_HAND:
        td_right = task_data.asdict()
        td_right["notes_left"] = []
        td_right["practice_mode"] = PracticeMode.RIGHT_HAND
        td_right = TaskData(**td_right)
        return [td_right], ["SPLIT_HANDS_R"]

    if practice_mode == PracticeMode.LEFT_HAND:
        td_left = task_data.asdict()
        td_left["notes_right"] = []
        td_left["practice_mode"] = PracticeMode.LEFT_HAND
        td_left = TaskData(**td_left)
        return [td_left], ["SPLIT_HANDS_L"]

    if practice_mode == PracticeMode.SINGLE_NOTE:
        new_td = task_data.asdict()
        # transform all notes to one pitch (62/50)
        new_td["notes_right"] = [TaskNote(start, 62, duration)
                                 for start, pitch, duration in new_td["notes_right"]]
        new_td["notes_left"] = [TaskNote(start, 50, duration)
                                for start, pitch, duration in new_td["notes_left"]]
        new_td["practice_mode"] = PracticeMode.SINGLE_NOTE
        return [TaskData(**new_td)], ["SINGLE_NOTE"]

    if practice_mode == PracticeMode.SLOWER:
        new_td = task_data.asdict()
        new_td["bpm"] -= 20
        new_td["practice_mode"] = PracticeMode.SLOWER
        return [TaskData(**new_td)], ["SLOWER"]

    raise ValueError(f"Unexpected practice mode {practice_mode}!")
