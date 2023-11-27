#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import functools
import tkinter as tk

from task_generation.midi_to_task import midi2taskdata

from task_generation.task_parameters import TaskParameters
from task_generation.task import TargetTask
from task_generation.task_data import TaskData
from task_generation.practice_modes import PracticeMode


class Scheduler:
    def __init__(self):
        self.task_queue = list()  # type: list[TargetTask]
        self.task_queue_index = 0

        # if there are tasks in here they have to be executed
        self.task_movement = list()  # type: list[(str, TaskData)]
        self.task_movement_eval_func = functools.partial(print, "TASK_MOVEMENT_ERRORS:")

    def in_task_movement(self):
        return len(self.task_movement) > 0

    def new_task_forced_practice_sequence_prior(self, task_parameters_fallback,
                                                list_of_practice_modes):
        self.queue_new_target_task(task_parameters_fallback)

        for pm in list_of_practice_modes:
            self._current_target_task().queue_practice_mode(pm)

        self._current_target_task().single_target_eval_at_end()
        self.task_movement = copy.deepcopy(self._current_target_task().subtask_queue)

    def queue_new_target_task(self, task_parameters: TaskParameters) -> TaskData:
        target_task = TargetTask.from_task_parameters(task_parameters)
        self.task_queue.append(target_task)
        self.task_queue_index = len(self.task_queue) - 1
        return self.current_task_data()

    def queue_new_target_task_from_midi(self, midifile_path: str):
        task_data = midi2taskdata(midifile_path)
        target_task = TargetTask(task_data)
        self.task_queue.append(target_task)
        self.task_queue_index = len(self.task_queue) - 1
        return self.current_task_data()

    def _current_target_task(self) -> TargetTask:
        return self.task_queue[self.task_queue_index]

    def current_task_data(self) -> TaskData:
        if self.in_task_movement():
            print("(SCHEDULER) IN TASK MOVEMENT")
            return self.task_movement[0][1]

        print("(SCHEDULER) task queue:", self.task_queue, "[", self.task_queue_index, "]")
        return self._current_target_task().current_task_data()

    def get_next_task(self, task_parameters) -> TaskData:
        if len(self.task_queue) == 0:
            return self.queue_new_target_task(task_parameters)

        if self._current_target_task().next_subtask_exists():
            return self._current_target_task().next_subtask()

        if self.next_task_exists():
            self.task_queue_index += 1
            return self.current_task_data()

        return self.queue_new_target_task(task_parameters)

    def get_previous_task(self):
        # try to go to the prev subtask of the current target task
        if self._current_target_task().previous_subtask_exists():
            return self._current_target_task().previous_subtask()

        if self.previous_task_exists():
            self.task_queue_index -= 1
            return self.current_task_data()

        raise ValueError("There is no previous task!")

    def queue_practice_mode(self, practice_mode):
        self._current_target_task().queue_practice_mode(practice_mode)

    def info(self):
        pass

    def previous_task_exists(self):
        if self.in_task_movement():
            return False

        if len(self.task_queue) == 0:
            return False
        else:
            return self._current_target_task().previous_subtask_exists() or \
                   self.task_queue_index > 0

    def next_task_exists(self):
        if self.in_task_movement():
            # we want to control everything while in task movement
            return False

        if len(self.task_queue) == 0:
            return False
        else:
            return self._current_target_task().next_subtask_exists() or \
                   self.task_queue_index < len(self.task_queue) - 1

    # add new task to queue from task_data and task_parameters
    def add_task_from_file(self, task_data):
        current_target_task = TargetTask(task_data)
        self.task_queue.append(current_target_task)
        self.task_queue_index = len(self.task_queue) - 1
        return self.current_task_data()

    def clear_queue(self):
        self.task_queue.clear()
        self.task_queue_index = 0
        self.task_movement.clear()


def choosePracticeMode(tk_root):
    global_var_name = "_NEXT_TASK_GEN_OPTION"

    new_window = tk.Toplevel(tk_root)

    def set_option(option):
        def set_option_actual(option):
            globals()[global_var_name] = option
            new_window.destroy()

        return functools.partial(set_option_actual, option)

    b = tk.Button(new_window, text="NEW TASK", command=set_option("NEW_TASK"))
    b.pack(side=tk.TOP, padx=5, pady=15)

    b = tk.Button(new_window, text="Next node", command=set_option("NEXT_LEVEL"))
    b.pack(side=tk.TOP, padx=5, pady=15)

    l = tk.Label(new_window, text="Same piece, but practice mode:")
    l.pack(side=tk.TOP, padx=5, pady=1)

    for pm in PracticeMode:
        b = tk.Button(new_window, text=pm.name, command=set_option(pm),
                      padx=5, pady=5)
        b.pack(side=tk.TOP)
        b.bind()

    tk_root.wait_window(new_window)

    try:
        val = globals()[global_var_name]
        del globals()[global_var_name]
    except:
        val = "X"

    return val


def threshold_info(tk_root):
    new_window = tk.Toplevel(tk_root)

    l = tk.Label(new_window,
                 text="I think this needs some more practise. How about we try out different practise "
                      "modes and learn together.")
    l.pack(side=tk.TOP, padx=5, pady=1)

    b = tk.Button(new_window, text="Okay", command=lambda: new_window.destroy())
    b.pack(side=tk.TOP, padx=5, pady=15)


def complexity_error(tk_root):
    new_window = tk.Toplevel(tk_root)

    l = tk.Label(new_window,
                 text="Error: To use the predefined complexity levels, please start the Dynamic Difficulty Adjustment!")
    l.pack(side=tk.TOP, padx=5, pady=1)

    b = tk.Button(new_window, text="Okay", command=lambda: new_window.destroy())
    b.pack(side=tk.TOP, padx=5, pady=15)
