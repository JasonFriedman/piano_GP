#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
# from midiInput import NoteInfo
from error_calc.explanation import NoteExtra, NoteMissing
from collections import namedtuple
NoteInfo = namedtuple("NoteInfo", ["pitch", "velocity", "note_on_time", "note_off_time"])
from task_generation.task_data import TaskData
from task_generation.generator import TaskNote
from task_generation.note_range_per_hand import NoteRangePerHand



def TaskDataFromNotes(left=None, right=None):
    left = left or list()
    right = right or list()
    td = TaskData(time_signature=(4,4), 
                    number_of_bars=99, 
                    note_range=NoteRangePerHand.C_TO_G, 
                    notes_right=left, #not used but checked with len i think
                    notes_left=right, #not used but checked with len i think
                    bpm=120)
    td.midi.register_midi_events(left, right)
    return td


def simple_scale():
    LENGTH = 8
    notes = list()
    for pitch, start_time in zip(range(LENGTH), range(LENGTH)):
        notes.append(NoteInfo(pitch, 64, start_time*2, start_time*2+1))
        
    return notes


def simple_rhythmic():
    import random
    lengths = [1, 0.5, 0.25]
    n_notes = 3
    pitch = 0
    
    time = 0
    notes = list()
    for length in lengths:
        for i in range(n_notes):
            
            notes.append(NoteInfo(pitch, 100, time, time+length))
            time += length*2
            
    return notes

def drop_notes(actual, n_iter=2, verbose=True):
    import random
    
    for i in range(n_iter):
        idx = random.randint(0, len(actual)-1)
        dropped_note = actual.pop(idx)
        # explanation.append()
        if verbose:
            print("Dropped", dropped_note)
    
    return actual

def repeat_notes(actual, n_iter=2, n_reps=1, verbose=True):
    import random
    already_repeated = set()
    for i in range(n_iter):
        idx = random.randint(0, len(actual)-1)
        note_to_repeat = actual[idx]
        while note_to_repeat in already_repeated:
            idx = random.randint(0, len(actual)-1)
            note_to_repeat = actual[idx]
        
        already_repeated.add(note_to_repeat)
        actual.pop(idx)
        
        if verbose:
            print(f"Repeating (x{n_reps})", note_to_repeat)
        
        n = note_to_repeat
        time_for_all_notes = n.note_off_time - n.note_on_time
        dt = time_for_all_notes / (n_reps +1) / 2
        
        for i in range(n_reps+1):
            ix2 = i*2
            new_note = NoteInfo(n.pitch, n.velocity, 
                            note_on_time =n.note_on_time + ix2*dt, 
                            note_off_time=n.note_on_time + (ix2+1)*dt)
            actual.insert(idx, new_note)
            already_repeated.add(new_note)
    
    return actual
       
def wrong_pitch(actual, n_iter=2, max_off=6, verbose=True):     
    import random
    # already_changed = set()
    for i in range(n_iter):
        idx = random.randint(0, len(actual)-1)
        note_to_change = actual.pop(idx)
        
        new_pitch = note_to_change.pitch + random.randint(1, max_off) * (-1**random.randint(0,1))
        
        n = note_to_change
        actual.insert(idx, NoteInfo(new_pitch, n.velocity, n.note_on_time, n.note_off_time))
        
        if verbose:
            print(f"Changed Pitch from {n.pitch} to {new_pitch} for", n)
    
    return actual

def add_pause(actual, n_iter=2, verbose=True):
    import random
    # already_changed = set()
    PAUSE_DUR = 3 #seconds
    for i in range(n_iter):
        idx = random.randint(1, len(actual)-2)
        
        for i in range(idx, len(actual)):
            n = actual[i]
            actual[i] = NoteInfo(n.pitch, n.velocity, 
                                 n.note_on_time+PAUSE_DUR, 
                                 n.note_off_time+PAUSE_DUR)
            
    return actual


def test_evo_scale_drop():
    from error_calc.functions import computeErrorEvo as ce_evo
    
    results = list()
    for i in range(200):
        # target_notes = simple_scale() #simple_rhythmic
        target_notes = simple_rhythmic() 
        actual_notes = target_notes.copy()
        drop_notes(actual_notes)
        
        missing_time_ons = set(t.note_on_time for t in target_notes).difference(
                a.note_on_time for a in actual_notes)
        
        
        explanation, error, _, _ = ce_evo(
            TaskDataFromNotes(right=target_notes),
                                    actual_notes, False, False)
        
        selected_time_ons = set()
        for note in explanation:
            if type(note) == NoteMissing:
                selected_time_ons.add(note.note_on_time_target)
                
        if len(missing_time_ons.difference(selected_time_ons)) == 0:
            results.append(1)
        else:
            results.append(0)
    
    print(sum(results)/len(results))
        

if __name__ == "__main__":
    target_notes = simple_scale() #simple_rhythmic
    # target_notes = simple_rhythmic() 
    
    actual_notes = target_notes.copy()
    
    # drop_notes(actual_notes)
    # repeat_notes(actual_notes)
    # wrong_pitch(actual_notes)
    add_pause(actual_notes)
    
    actual_notes = sorted(actual_notes, key=lambda n: n.note_on_time)
    
    print("TARGET_NOTES:")
    print(target_notes)
    print("ACTUAL_NOTES:")
    print(actual_notes)
    
    from error_calc.functions import computeErrorLV  as ce_lv
    from error_calc.functions import computeErrorEvo as ce_evo
    
    from functools import partial
    # ce_evo = partial(ce_evo, interactive=True)
    
    error_funcs = dict(
                        # old=ce_old, ## too old
                        levenshtein=ce_lv,
                        evo=ce_evo,    
                       )
    
    for key, func in error_funcs.items():
        new_func = partial(func, 
                           plot=True, inject_explanation=False)
        
            
        error_funcs[key] = new_func
    
    error_dict = dict()
    for name, computeError in error_funcs.items():
        print(name)
        start_time = time.time()
        error = computeError(
            TaskDataFromNotes(right=target_notes), 
            actual_notes)[1]
        # print("ERROR:", error)
        # error_dict[name] = error
        
        print("took {:.2f}s".format(time.time()-start_time))
        print()
        
    import pprint
    pprint.pprint(error_dict)
    # print(computeError(target_notes, actual_notes))
    # output_note_list, error = computeError(target_notes, actual_notes)
    # test_evo_scale_drop()