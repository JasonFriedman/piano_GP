import mido
import math

from collections import namedtuple

from task_generation.task_data import TaskData
from task_generation.task_parameters import TaskParameters
from task_generation.note_range_per_hand import NoteRangePerHand

TaskNote = namedtuple("TaskNote", "start pitch duration")


def midi2taskdata(midifile_path):
    """
    function to create TaskData from midifile
    @param midifile_path: path to the midifile to be transformed
    @return: generated TaskData
    """

    # load midifile
    midi = mido.MidiFile(midifile_path, clip=True)

    bpm, time_signature, n_beats = -1, -1, -1
    time1 = 0
    for msg in midi.tracks[1]:
        time1 += msg.time

    time2 = 0
    if len(midi.tracks) > 2:
        for msg in midi.tracks[2]:
            time2 += msg.time

    for msg in midi.tracks[0]:
        if msg.type == 'set_tempo':
            bpm = mido.tempo2bpm(msg.tempo)
        if msg.type == 'time_signature':
            time_signature = (msg.numerator, msg.denominator)

    # calculate the total number of bars from the sum of midi ticks and the time signature
    n_beats = max(time1, time2) / midi.ticks_per_beat
    no_of_bars = math.ceil(n_beats / time_signature[0]) + 2

    # set left and right hand
    right, left = len(midi.tracks) >= 2, len(midi.tracks) > 2

    # extract messages related to notes in right and left hand
    messages = []
    if len(midi.tracks) == 2:
        messages.append(midi.tracks[1])
    elif len(midi.tracks) > 2:
        messages.append(midi.tracks[1])
        messages.append(midi.tracks[2])

    # create TaskNotes from midi tracks
    notes = dict(left=[], right=[])
    for track in messages:
        passed_time = time_signature[0]
        for i in range(len(track) - 1):
            if track[i].type != 'note_on' and track[i].type != 'note_off':
                continue
            passed_time += track[i].time / midi.ticks_per_beat
            if track[i].velocity != 0 and track[i].type == 'note_on':
                if track[i].channel == 0:
                    notes["right"].append(
                        TaskNote(passed_time, track[i].note, float(track[i + 1].time) / midi.ticks_per_beat))
                elif track[i].channel == 1:
                    notes["left"].append(
                        TaskNote(passed_time, track[i].note, float(track[i + 1].time) / midi.ticks_per_beat))
    
    # parse extracted information to TaskParameters
    task_parameter = TaskParameters(
        timeSignature=time_signature,
        maxNotesPerBar=16,
        noOfBars=no_of_bars,
        note_range_right=NoteRangePerHand.ONE_OCTAVE,  # where does this come from?
        note_range_left=NoteRangePerHand.ONE_OCTAVE,
        right=right,
        left=left,
        alternating=False,
        bpm=None # bpm
    )

    task_data = TaskData(
        parameters=task_parameter,
        time_signature=time_signature,
        number_of_bars=no_of_bars,
        notes_left=notes["left"],
        notes_right=notes["right"],
        bpm=None # bpm
    )

    return task_data
