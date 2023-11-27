#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import enum

class NoteRangePerHand(enum.Enum):
    UNKOWN = enum.auto()
    
    ONE_NOTE = enum.auto()
    TWO_NOTES = enum.auto()
    THREE_NOTES = enum.auto()
    FOUR_NOTES = enum.auto()
    C_TO_G = enum.auto()
    C_DUR= enum.auto()
    BLUES = enum.auto()
    ONE_OCTAVE_BLACK = enum.auto()
    ONE_OCTAVE = enum.auto()
    
noteRangePerHandDescription = ["One note (C)", "Two notes (C,D)", "Three Notes (C,D,E)", "Four Notes (C, D, E, F)",
                               "Five Notes (C-G static finger mapping)",
                               "C-Dur", "Blues",
                               "One octave (only black keys)", "One octave"
                               ]
#noteRangePerHandDescription = ["One note (C)", "Two notes (C,D)", "Three Notes (E,F,G)", "Four Notes (C, E, F,G)",
#                               "Notes C-G (static finger mapping)",
#                               "C-Dur", "Blues",
#                               "One octave (only black keys)", "One octave"
#                               ]

noteRangeMap = {const: desc for const, desc in 
                zip(list(NoteRangePerHand)[1:], noteRangePerHandDescription)}
noteRangeMap.update(                   
                    {desc: const for const, desc in 
                zip(list(NoteRangePerHand)[1:], noteRangePerHandDescription)}
                    )

def get_pitchlist(note_range):

    # Typecast to string, bc weird error gives false comparison otherwise
    if str(note_range) == str(NoteRangePerHand.ONE_NOTE):
        pitchesList = [0]
    elif str(note_range) == str(NoteRangePerHand.TWO_NOTES):
        pitchesList = [0, 2]
    elif str(note_range) == str(NoteRangePerHand.THREE_NOTES):
        pitchesList = [0, 2, 4]
        #pitchesList = [4,5,7]
    elif str(note_range) == str(NoteRangePerHand.FOUR_NOTES):
        pitchesList = [0, 2, 4, 5]
        #pitchesList= [0,4,5,7]
    elif str(note_range) == str(NoteRangePerHand.C_TO_G):
        pitchesList = [0, 2, 4, 5, 7]
    elif str(note_range) == str(NoteRangePerHand.C_DUR):
        pitchesList = [0,2,4,5,7,9,11]
    elif str(note_range) == str(NoteRangePerHand.BLUES):
        pitchesList = [0,3,5,6,7,10,11]
    elif str(note_range) == str(NoteRangePerHand.ONE_OCTAVE_BLACK):
        pitchesList = [1,3,6,8,10]
    elif str(note_range) == str(NoteRangePerHand.ONE_OCTAVE):
        pitchesList = list(range(0, 12))
    else:
        raise ValueError(f"got unexpected note_range {repr(note_range)}!")
        
    return pitchesList

# base determines whether the pitch list is for the left or the right hand.
def transpose (pitchesList, base_note= 60):        # base_note = 48 #C3

     return [base_note + p for p in pitchesList]