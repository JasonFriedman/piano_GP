#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random

from task_generation.note_range_per_hand import get_pitchlist, transpose
from collections import namedtuple
from collections.abc import Iterable
from task_generation.task_parameters import TaskParameters
from task_generation.task_data import TaskData

TaskNote = namedtuple("TaskNote", "start pitch duration")

INTRO_BARS = 1  # no. of empty first bars for metronome intro
ACROSS_BARS = False  # allow notes to reach across two bars


def flatten(x):
    if isinstance(x, Iterable):
        return [a for i in x for a in flatten(i)]
    else:
        return [x]


def generate_task(task_parameters: TaskParameters) -> TaskData:
    return _generate_task_v1(task_parameters)


def _generate_task_v1(task_parameters):
    numerator, denominator = task_parameters.timeSignature

    # adjust no. of bars (in case of intro bars)
    bars = task_parameters.noOfBars + INTRO_BARS

    data = dict(left=[], right=[])

    def getpitches(note_range, base):
        nl = get_pitchlist(note_range)
        tnl = transpose(nl, base)
        return tnl

    def get_timesteps(hand, note_range, base):
        pitches = getpitches(note_range, base)
        print("pitchlist", pitches)
        ### CHOOSE TIME_AT_STARTSTEPS ###

        timesteps = []
        minNoteVal = min(task_parameters.noteValues)

        # randomly generate the chosen number of timesteps (notes) per bar
        stepRange = [temp for temp in range(numerator) if temp % (minNoteVal * numerator) == 0]
        print("stepRange", stepRange)
        for bar in range(task_parameters.noOfBars - 1):  # last bar is for extra notes
            # determine no. of notes in this bar
            noOfNotes = random.choice(range(1,
                                            task_parameters.maxNotesPerBar + 4))  # add a lot to maxNotesPerBar to get less pauses
            noOfNotes = min(noOfNotes, len(stepRange))

            # shift step numbers
            shift = (bar + INTRO_BARS) * numerator
            steps = [temp + shift for temp in stepRange]
            print("steps", steps)

            new_steps = [steps[0]]  # add note at beginning of every bar so there are less pauses
            new_steps.append(random.sample(steps[1:], noOfNotes - 1))
            flat_steps = [a for i in new_steps for a in flatten(i)]
            timesteps.append(flat_steps)

        # flatten and sort list
        timesteps = sorted([item for sublist in timesteps for item in sublist])

        # append dummy element to avoid additional bar
        timesteps.append(bars * numerator)

        # add music (piano) notes

        # custom for-loop
        t = 0
        while t < (len(timesteps) - 1):
            # compute maximum note length until next note
            maxNoteVal = (timesteps[t + 1] - timesteps[t]) / denominator

            # compute maximum note length until next bar
            if not ACROSS_BARS:
                maxToNextBar = 1 - ((timesteps[t] % denominator) / denominator)
                maxNoteVal = min([maxNoteVal, maxToNextBar])

            # calculate possible note values at current time step
            possNoteValues = [v for v in task_parameters.noteValues if v <= maxNoteVal]
            # if list is empty, increment time step by 1 and try again
            if not possNoteValues:
                print(t, timesteps[t], maxNoteVal)
                timesteps[t] = timesteps[t] + 1
                continue

            # introduce some randomness, so large values are more equally likely getting picked
            if random.random() > 0.4:
                duration = random.choice(possNoteValues)
            else:
                duration = max(possNoteValues)
            pitch = random.choice(pitches)

            data[hand].append(TaskNote(timesteps[t], pitch, duration * denominator))

            if duration == 1 / 8:
                ## if the duration is 1/8, add a note right after to differentiate it more from 1/4
                pitch = random.choice(pitches)
                data[hand].append(TaskNote(timesteps[t] + 0.5, pitch, duration * denominator))

            t += 1

    # for hand in hands:
    if task_parameters.left:
        get_timesteps("left", task_parameters.note_range_left, 48)  # C3)
    if task_parameters.right:
        get_timesteps("right", task_parameters.note_range_right, 60)

    hands = list()
    if task_parameters.left:
        hands.append("left")
    if task_parameters.right:
        hands.append("right")

    # the first bar is empty -> offset of 4
    offset = 4

    # play with both hands alternating, instead of together at the same time
    if task_parameters.alternating:
        if task_parameters.left and task_parameters.right:  # only alternating if task actually involves both hands
            for hand in ["left", "right"]:
                if hand == "left":
                    # calculate positions in the score in which only the left hand should play and save those in list note_starts
                    note_starts = []
                    for bar in range(task_parameters.noOfBars - 1):
                        # if it's an uneven bar the left hand will play
                        if bar % 2 != 0:
                            # the first position in a bar is calculated (start_pos)
                            start_pos = offset + bar * numerator
                            note_starts.extend(
                                [start_pos, start_pos + 1, start_pos + 2, start_pos + 3])
                    print("left", note_starts)
                else:
                    # calculate positions in the score in which only the right hand should play and save those in list note_starts
                    note_starts = []
                    for bar in range(task_parameters.noOfBars - 1):
                        # if it's an even bar the right hand will play
                        if bar % 2 == 0:
                            # the first position in a bar is calculated (start_pos)
                            start_pos = offset + bar * numerator
                            note_starts.extend(
                                [start_pos, start_pos + 1, start_pos + 2, start_pos + 3])
                    print("right", note_starts)
                # remove all notes that are in bars/positions, which should be empty
                remove = []
                for task in data[hand]:
                    if task.start not in note_starts:
                        remove.append(task)
                for item in remove:
                    data[hand].remove(item)

    return TaskData(parameters=task_parameters, time_signature=task_parameters.timeSignature,
                    number_of_bars=bars,
                    bpm=float(task_parameters.bpm), notes_left=data["left"],
                    notes_right=data["right"])  # note_range = task_parameters.note_range,
